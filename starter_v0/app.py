from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from agent import ResearchAgent
from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from providers import make_provider
from run_eval import (
    DATA_DIR,
    case_messages,
    evaluate_phase_b,
    load_cases,
    load_dataset_info,
    summarize,
    validate_expected_tools,
)
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

TRANSCRIPTS_DIR = ROOT / "transcripts"
RUNS_DIR = ROOT / "runs"
EVAL_GROUP_PATH = DATA_DIR / "eval_group.json"

PROVIDERS = ["openai", "openrouter", "anthropic", "gemini"]

# Bảng tool hiển thị cho người xem demo — khớp với tools/__init__.py::TOOL_FUNCTIONS
# và artifacts/tools.yaml. Không đưa social_search/send vào đây: hai tool đó không
# thuộc bộ tool chính thức của persona "Research Paper Scout".
TOOL_REFERENCE = [
    ("clarify", "Hỏi lại khi thiếu chủ đề, paper ID, URL, tiêu chí lựa chọn hoặc thuật ngữ cần giải thích"),
    ("papers", "Tìm paper trên arXiv theo chủ đề"),
    ("paper_text", "Đọc nhanh một số trang đầu của paper"),
    ("paper_reader", "Đọc toàn bộ PDF, chia nội dung theo trang và section"),
    ("paper_sections", "Trích riêng Method, Experiments, Results và Limitations cùng bằng chứng"),
    ("explain_terms", "Giải thích thuật ngữ dựa trên ngữ cảnh trong paper và nguồn tham khảo"),
    ("lookup", "Tìm paper, benchmark, blog hoặc thông tin liên quan trên web"),
    ("fetch", "Đọc nội dung từ một URL cụ thể không phải arXiv"),
    ("policy", "Tra quy định nội bộ về nghiên cứu, trích dẫn và quyền riêng tư"),
    ("format", "Định dạng kết quả thành brief, bullet hoặc báo cáo theo section"),
    ("timeline", "Xem các bài đăng gần đây từ tác giả hoặc research lab cụ thể"),
]

STATUS_ICON = {"ok": "✅", "error": "❌", "waiting_for_user": "⏸️"}
TURN_BADGE = {
    "answered": "🟢 answered",
    "waiting_for_user": "🟡 waiting_for_user",
    "max_tool_rounds": "🟠 max_tool_rounds",
    "provider_error": "🔴 provider_error",
}

st.set_page_config(page_title="Research Paper Scout", page_icon="📄", layout="wide")


# --------------------------------------------------------------------------- #
# Session state helpers
# --------------------------------------------------------------------------- #

def init_state() -> None:
    st.session_state.setdefault("config_locked", False)
    st.session_state.setdefault("transcript", None)
    st.session_state.setdefault("transcript_path", None)
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("active_config", {})


def new_session() -> None:
    st.session_state["config_locked"] = False
    st.session_state["transcript"] = None
    st.session_state["transcript_path"] = None
    st.session_state["history"] = []
    st.session_state["active_config"] = {}


# --------------------------------------------------------------------------- #
# Sidebar: provider/version config + tool reference
# --------------------------------------------------------------------------- #

def sidebar_config() -> dict[str, Any]:
    st.sidebar.header("⚙️ Cấu hình phiên")

    if st.session_state["config_locked"]:
        cfg = st.session_state["active_config"]
        st.sidebar.success("Phiên đang chạy — cấu hình bị khoá để transcript nhất quán.")
        st.sidebar.markdown(
            f"- **provider**: `{cfg['provider']}`\n"
            f"- **model**: `{cfg['selected_model']}`\n"
            f"- **version**: `{cfg['version']}`\n"
            f"- **artifact_version**: `{cfg['artifact_version']}`"
        )
        if st.sidebar.button("🔄 Bắt đầu phiên hội thoại mới", use_container_width=True):
            new_session()
            st.rerun()
        render_tool_reference()
        return cfg

    provider = st.sidebar.selectbox(
        "Model provider", PROVIDERS, index=PROVIDERS.index("openai")
    )
    model = st.sidebar.text_input("Model (để trống = default của provider)", value="")
    version = st.sidebar.text_input(
        "Version label", value="v0", help="Nhãn version dùng cho eval/report, ví dụ v0/v1/v2/v3."
    )
    system_prompt_rel = st.sidebar.text_input(
        "system_prompt.md",
        value=str((ARTIFACTS_DIR / "system_prompt.md").relative_to(ROOT)),
    )
    tools_rel = st.sidebar.text_input(
        "tools.yaml",
        value=str((ARTIFACTS_DIR / "tools.yaml").relative_to(ROOT)),
    )
    max_tool_rounds = st.sidebar.number_input("max_tool_rounds", min_value=1, max_value=10, value=4)
    history_window = st.sidebar.number_input("history_window", min_value=0, max_value=20, value=5)

    system_prompt_path = (ROOT / system_prompt_rel).resolve()
    tools_path = (ROOT / tools_rel).resolve()

    st.sidebar.markdown("**artifact_version xem trước:**")
    try:
        preview = build_artifact_version(version, system_prompt_path, tools_path)
        st.sidebar.code(preview.artifact_version, language="text")
    except FileNotFoundError as exc:
        st.sidebar.error(f"Không đọc được artifact: {exc}")

    render_tool_reference()

    return {
        "provider": provider,
        "model": model or None,
        "version": version,
        "system_prompt_path": system_prompt_path,
        "tools_path": tools_path,
        "max_tool_rounds": int(max_tool_rounds),
        "history_window": int(history_window),
    }


def render_tool_reference() -> None:
    with st.sidebar.expander(f"🧰 Tool đang dùng ({len(TOOL_REFERENCE)})", expanded=False):
        st.table({"tool": [t for t, _ in TOOL_REFERENCE], "chức năng": [d for _, d in TOOL_REFERENCE]})


# --------------------------------------------------------------------------- #
# Transcript / agent turn plumbing (reuses chat.py's run_model_tool_loop)
# --------------------------------------------------------------------------- #

def ensure_transcript(cfg: dict[str, Any]) -> str | None:
    """Create the transcript + live provider for this browser session, once. Returns an error message, if any."""
    if st.session_state["transcript"] is not None:
        return None

    try:
        system_prompt_text = cfg["system_prompt_path"].read_text(encoding="utf-8")
        tool_declarations = load_tool_declarations(cfg["tools_path"])
    except (FileNotFoundError, OSError) as exc:
        return f"Không đọc được artifact: {exc}"

    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(cfg["provider"])
    selected_model = cfg["model"] or getattr(provider, "default_model", None)
    artifact_version = build_artifact_version(cfg["version"], cfg["system_prompt_path"], cfg["tools_path"])

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(cfg["version"]), safe_slug(cfg["provider"]), timestamp])
    transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": cfg["provider"],
        "model": selected_model,
        "system_prompt": str(cfg["system_prompt_path"]),
        "tools": str(cfg["tools_path"]),
        "history_window": cfg["history_window"],
        "max_tool_rounds": cfg["max_tool_rounds"],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    st.session_state["transcript"] = transcript
    st.session_state["transcript_path"] = transcript_path
    st.session_state["active_config"] = {
        **cfg,
        "system_prompt_text": system_prompt_text,
        "openai_tools": openai_tools,
        "provider_obj": provider,
        "selected_model": selected_model,
        "artifact_version": artifact_version.artifact_version,
    }
    st.session_state["config_locked"] = True
    return None


def handle_user_message(user_text: str) -> None:
    cfg = st.session_state["active_config"]
    transcript = st.session_state["transcript"]
    turn_index = len(transcript["turns"]) + 1

    messages = [
        {"role": "system", "content": cfg["system_prompt_text"]},
        *trim_history(st.session_state["history"], cfg["history_window"]),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
        "artifact_version": cfg["artifact_version"],
    }

    try:
        result = run_model_tool_loop(
            provider=cfg["provider_obj"],
            messages=messages,
            tools=cfg["openai_tools"],
            model=cfg["model"],
            max_tool_rounds=cfg["max_tool_rounds"],
        )
        turn_record.update(result)
        assistant_text = result["assistant_text"]
        st.session_state["history"].append({"role": "user", "content": user_text})
        st.session_state["history"].append({"role": "assistant", "content": assistant_text})
    except Exception as exc:
        turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(st.session_state["transcript_path"], transcript)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def status_of(event: dict[str, Any]) -> str:
    result = event.get("result")
    if isinstance(result, dict):
        if result.get("awaiting_user"):
            return "waiting_for_user"
        if result.get("error"):
            return "error"
    return "ok"


def render_trace(rounds: list[dict[str, Any]]) -> None:
    for r in rounds:
        calls = r.get("tool_calls", [])
        label = f"Round {r['round']} · {len(calls)} tool call(s)" if calls else f"Round {r['round']} · trả lời trực tiếp"
        with st.expander(label, expanded=False):
            if not calls:
                st.caption(r.get("assistant_text") or "(không gọi tool)")
            for call, event in zip(calls, r.get("tool_results", [])):
                st_status = status_of(event)
                st.markdown(f"{STATUS_ICON[st_status]} **`{call['name']}`** — status: `{st_status}`")
                st.json({"args": call.get("args"), "result": event.get("result")})


def render_turn(turn: dict[str, Any]) -> None:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        badge = TURN_BADGE.get(turn.get("status", ""), turn.get("status", "?"))
        st.caption(f"{badge} · turn {turn['turn_index']} · artifact_version `{turn.get('artifact_version', '?')}`")
        if turn.get("status") == "provider_error":
            st.error(turn.get("error", "Unknown provider error"))
        else:
            st.write(turn.get("assistant_text") or "(không có nội dung)")
        if turn.get("rounds"):
            render_trace(turn["rounds"])


def render_chat_view(cfg: dict[str, Any]) -> None:
    st.subheader("📄 Research Paper Scout")
    st.caption(
        "AI chatbot tìm kiếm & tóm tắt paper học thuật — khám phá paper trên arXiv, đọc toàn văn, "
        "trích Method/Experiments/Results/Limitations, giải thích thuật ngữ, và tra cứu web/chính sách "
        "nội bộ khi cần."
    )

    transcript = st.session_state["transcript"]
    if transcript:
        st.info(
            f"transcript: `{transcript['transcript_id']}` · artifact_version: "
            f"`{transcript['artifact_version']}` · provider: `{transcript['provider']}` · "
            f"model: `{transcript['model']}`"
        )
        for turn in transcript["turns"]:
            render_turn(turn)
    else:
        st.info(
            "Chưa có tin nhắn nào. Gửi câu hỏi để bắt đầu — cấu hình ở sidebar sẽ bị khoá lại cho "
            "phiên/transcript này."
        )

    user_text = st.chat_input(
        "Hỏi về một chủ đề nghiên cứu, một paper arXiv cụ thể, hoặc một thuật ngữ..."
    )
    if user_text:
        error = ensure_transcript(cfg)
        if error:
            st.error(error)
        else:
            with st.spinner("Agent đang xử lý..."):
                handle_user_message(user_text)
            st.rerun()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def render_compare_view() -> None:
    st.subheader("📊 So sánh version")

    st.markdown("#### Eval runs (`runs/*.json`)")
    run_files = sorted(RUNS_DIR.glob("*.json")) if RUNS_DIR.exists() else []
    rows = []
    for path in run_files:
        data = load_json(path)
        if not data:
            continue
        summary = data.get("summary", {})
        rows.append({
            "run_file": path.name,
            "version": data.get("version"),
            "artifact_version": data.get("artifact_version"),
            "phase": data.get("phase"),
            "suite": data.get("suite"),
            "provider": data.get("provider"),
            "case_accuracy": summary.get("case_accuracy"),
            "tool_routing_accuracy": summary.get("tool_routing_accuracy"),
            "argument_accuracy": summary.get("argument_accuracy"),
            "multiturn_accuracy": summary.get("multiturn_accuracy"),
            "provider_error_cases": summary.get("provider_error_cases"),
            "measured_cases": summary.get("measured_cases"),
            "total_cases": summary.get("total_cases"),
        })
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.caption("Chưa có run nào trong `runs/`. Chạy `run_eval.py` để có dữ liệu.")

    st.markdown("#### Cùng một câu hỏi qua nhiều version (`transcripts/*.transcript.json`)")
    transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.transcript.json")) if TRANSCRIPTS_DIR.exists() else []
    turns_by_query: dict[str, list[dict[str, Any]]] = {}
    for path in transcript_files:
        data = load_json(path)
        if not data:
            continue
        for turn in data.get("turns", []):
            query = (turn.get("user") or "").strip()
            if not query:
                continue
            turns_by_query.setdefault(query, []).append({
                "transcript_id": data.get("transcript_id"),
                "version": data.get("version"),
                "artifact_version": data.get("artifact_version"),
                "provider": data.get("provider"),
                "status": turn.get("status"),
                "assistant_text": turn.get("assistant_text"),
                "tool_calls": sum(len(r.get("tool_calls", [])) for r in turn.get("rounds", [])),
            })

    scenario_options = sorted(q for q, v in turns_by_query.items() if len(v) > 1)
    if not scenario_options:
        st.caption(
            "Chưa có scenario nào được hỏi lại ở ≥2 version. Dùng nút 'Bắt đầu phiên hội thoại mới' để "
            "đổi version rồi hỏi lại đúng cùng một câu để so sánh tại đây."
        )
        return

    chosen = st.selectbox("Chọn câu hỏi để so sánh", scenario_options)
    for entry in turns_by_query[chosen]:
        st.markdown(
            f"**version** `{entry['version']}` · **artifact_version** `{entry['artifact_version']}` · "
            f"**provider** `{entry['provider']}` · **status** `{entry['status']}` · "
            f"**tool calls** {entry['tool_calls']}"
        )
        st.write(entry["assistant_text"] or "(không có nội dung)")
        st.divider()


# --------------------------------------------------------------------------- #
# Eval group runner (reuses run_eval.py's own grading pipeline)
# --------------------------------------------------------------------------- #

def render_eval_group_view(cfg: dict[str, Any]) -> None:
    st.subheader("🧪 Test eval_group")
    st.caption(
        "Chạy trực tiếp các case trong `data/eval_group.json` bằng provider/version đang chọn ở "
        "sidebar, chấm PASS/FAIL bằng đúng logic của `run_eval.py`, và lưu run JSON vào `runs/` "
        "(sẽ xuất hiện ở tab So sánh version)."
    )

    try:
        dataset_info = load_dataset_info(EVAL_GROUP_PATH)
        cases = load_cases(EVAL_GROUP_PATH, "B")
    except (FileNotFoundError, KeyError, ValueError) as exc:
        st.error(f"Không đọc được {EVAL_GROUP_PATH}: {exc}")
        return
    if not cases:
        st.warning(f"{EVAL_GROUP_PATH} chưa có case nào ở phase B.")
        return

    try:
        tool_declarations = load_tool_declarations(cfg["tools_path"])
        validate_expected_tools(cases, tool_declarations, EVAL_GROUP_PATH)
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        return

    case_labels = {
        case["id"]: (
            f"{case['id']} ({'multi-turn' if 'turns' in case else 'single-turn'}) — "
            f"{case.get('metadata', {}).get('what_it_tests', '')}"
        )
        for case in cases
    }
    selected_ids = st.multiselect(
        "Chọn case cần chạy",
        options=list(case_labels.keys()),
        default=list(case_labels.keys()),
        format_func=lambda cid: case_labels[cid],
    )

    run_clicked = st.button("▶️ Chạy eval đã chọn", type="primary", disabled=not selected_ids)

    if run_clicked:
        selected_cases = [case for case in cases if case["id"] in selected_ids]
        openai_tools = to_openai_tools(tool_declarations)
        provider = make_provider(cfg["provider"])
        selected_model = cfg["model"] or getattr(provider, "default_model", None)
        try:
            system_prompt_text = cfg["system_prompt_path"].read_text(encoding="utf-8")
        except OSError as exc:
            st.error(f"Không đọc được system prompt: {exc}")
            return
        artifact_version = build_artifact_version(cfg["version"], cfg["system_prompt_path"], cfg["tools_path"])

        results: list[dict[str, Any]] = []
        progress = st.progress(0.0, text="Đang chạy eval...")
        for i, case in enumerate(selected_cases, start=1):
            progress.progress((i - 1) / len(selected_cases), text=f"Đang chạy {case['id']}...")
            agent = ResearchAgent(provider, system_prompt=system_prompt_text, tools=openai_tools, model=cfg["model"])
            try:
                tool_choice = None if case["expect"].get("no_tool") else "required"
                run = agent.run(case_messages(case), tool_choice=tool_choice)
                calls = [{"name": call.name, "args": call.args} for call in run.tool_calls]
                result = evaluate_phase_b(case, calls, run.text)
                tool_results = run.tool_results
            except Exception as exc:
                tool_results = []
                result = {
                    "passed": False,
                    "failure_type": "provider_error",
                    "case_failure_type": case.get("failure_type"),
                    "observed_mismatch": "provider_error",
                    "failures": [f"{type(exc).__name__}: {exc}"],
                    "actual_tool_calls": [],
                    "actual_text": None,
                    "routing_correct": False,
                    "args_correct": False,
                }
            results.append({
                "id": case["id"],
                "phase": case["phase"],
                "suite": "group",
                "case_suite": case.get("suite", "group"),
                "is_multiturn": "turns" in case,
                "metadata": case.get("metadata", {}),
                "input": case.get("input") or case.get("query") or case.get("turns"),
                "expect": case["expect"],
                "result": result,
                "tool_results": tool_results,
            })
        progress.progress(1.0, text="Hoàn tất.")
        progress.empty()

        summary = summarize(results)
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        now = datetime.now()
        run_id = "_".join([
            safe_slug(cfg["version"]), "B", "group", safe_slug(cfg["provider"]),
            now.strftime("%Y%m%dT%H%M%S%f"),
        ])
        payload = {
            "run_id": run_id,
            "version": cfg["version"],
            **artifact_version_dict(artifact_version),
            "phase": "B",
            "suite": "group",
            "provider": cfg["provider"],
            "model": selected_model,
            "system_prompt": str(cfg["system_prompt_path"]),
            "tools": str(cfg["tools_path"]),
            "eval_cases": str(EVAL_GROUP_PATH),
            **dataset_info,
            "generated_at": now.isoformat(timespec="seconds"),
            "summary": summary,
            "results": results,
        }
        out_path = RUNS_DIR / f"{run_id}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        st.session_state["last_eval_run"] = payload
        st.session_state["last_eval_run_path"] = out_path

    last_run = st.session_state.get("last_eval_run")
    if not last_run:
        st.caption("Chưa chạy eval nào trong phiên này.")
        return

    st.success(f"Đã lưu run: `{st.session_state['last_eval_run_path'].name}`")
    summary = last_run["summary"]
    cols = st.columns(4)
    cols[0].metric("case_accuracy", summary.get("case_accuracy"))
    cols[1].metric("tool_routing_accuracy", summary.get("tool_routing_accuracy"))
    cols[2].metric("argument_accuracy", summary.get("argument_accuracy"))
    multiturn = summary.get("multiturn_accuracy")
    cols[3].metric("multiturn_accuracy", multiturn if multiturn is not None else "—")
    st.caption(
        f"measured_cases: {summary.get('measured_cases')}/{summary.get('total_cases')} · "
        f"provider_error_cases: {summary.get('provider_error_cases')} · "
        f"artifact_version: `{last_run['artifact_version']}`"
    )

    for item in last_run["results"]:
        status = "✅ PASS" if item["result"]["passed"] else "❌ FAIL"
        header = f"{status} · {item['id']} · {item.get('metadata', {}).get('what_it_tests', '')}"
        with st.expander(header):
            st.markdown("**Input:**")
            st.json(item["input"])
            st.markdown("**Expected:**")
            st.json(item["expect"])
            st.markdown("**Actual tool calls:**")
            st.json(item["result"].get("actual_tool_calls"))
            if item["result"].get("actual_text"):
                st.markdown("**Actual text:**")
                st.write(item["result"]["actual_text"])
            if item["result"].get("failures"):
                st.markdown("**Failures:**")
                for failure in item["result"]["failures"]:
                    st.write(f"- {failure}")


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    init_state()
    cfg = sidebar_config()

    view = st.sidebar.radio(
        "Chế độ xem", ["💬 Chat", "🧪 Test eval_group", "📊 So sánh version"], index=0
    )
    if view == "💬 Chat":
        render_chat_view(cfg)
    elif view == "🧪 Test eval_group":
        render_eval_group_view(cfg)
    else:
        render_compare_view()


if __name__ == "__main__":
    main()
