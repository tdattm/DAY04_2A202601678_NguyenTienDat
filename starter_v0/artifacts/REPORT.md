# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: A3
- Members:
  - Lê Hồ Quang Huy — 2A202602026 — Tool Engineering Lead
  - Lã Phan Hoài An — 2A202601846 — Eval & QA Lead
  - Nguyễn Tiến Đạt — 2A202601678 — Prompt & Evaluation Lead
  - Kiều Phúc Huy — 2A202601056 — UI & Deployment Lead
  - Nguyễn Nam Phong — 2A202601320 — Report & Demo Lead
- Provider/model: OpenAI / `gpt-4o-mini`

### Role assignment

| Thành viên | MSSV | Role | Nhiệm vụ chính | Deliverable phụ trách |
|---|---|---|---|---|
| Lê Hồ Quang Huy | 2A202602026 | Tool Engineering Lead | Thiết kế và triển khai ít nhất một tool mới; viết `TOOL.md`; đăng ký tool trong `tools/__init__.py` và `artifacts/tools.yaml`; smoke-test implementation và kiểm tra lỗi thực thi của các tool/API. | `tools/<new_tool>/`, tool registry, tool declaration và bằng chứng smoke test |
| Lã Phan Hoài An | 2A202601846 | Eval & QA Lead | Thiết kế đúng 10 team eval case gồm 5 single-turn và 5 multi-turn; kiểm tra schema/expected behavior; chạy regression và review thủ công các mismatch hoặc tool result có lỗi. | `data/eval_group.json`, kết quả group eval và QA evidence |
| Nguyễn Tiến Đạt | 2A202601678 | Prompt & Evaluation Lead | Phân tích failed trace; tối ưu `system_prompt.md`/tool routing theo từng giả thuyết; chạy và so sánh `v0`–`v3`; quản lý metric, artifact hash và version history. | `artifacts/system_prompt.md`, `artifacts/version_log.csv`, `runs/*.json` và failure analysis |
| Kiều Phúc Huy | 2A202601056 | UI & Deployment Lead | Xây dựng UI tái sử dụng agent loop trong `chat.py`; hiển thị request/response, tool trace, args, result/error và artifact version; lưu transcript; triển khai URL để nhóm khác kiểm thử. | `app.py`, UI dependencies, `transcripts/*.transcript.json` và public demo URL |
| Nguyễn Nam Phong | 2A202601320 | Report & Demo Lead | Tổng hợp evidence thật vào Report A/B; chuẩn bị 3–5 scenario demo, câu hỏi mẫu, fallback run/transcript; điều phối rehearsal, showdown và final submission checklist. | `artifacts/REPORT.md`, demo script, rehearsal evidence và final gate |

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL:

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| single_01 | Tìm kiếm cơ bản với từ khóa | `papers` | PASS (`v8`) |
| single_02 | Bắt lỗi thiếu thông tin Paper ID | `clarify` | PASS (`v8`) |
| single_03 | Trích xuất chi tiết bằng tool mới paper_sections | `paper_sections` | PASS (`v8`) |
| single_04 | Giải thích chuyên sâu thuật ngữ trong paper | `explain_terms` | PASS (`v8`) |
| single_05 | Phân biệt paper_text (đọc lướt) vs paper_reader | `paper_text` | PASS (`v8`) |
| multi_01 | Luồng papers -> paper_reader | `paper_reader` | PASS (`v8`) |
| multi_02 | Luồng papers -> paper_sections | `paper_sections` | PASS (`v8`) |
| multi_03 | Luồng paper_sections -> explain_terms | `explain_terms` | PASS (`v8`) |
| multi_04 | Luồng paper_reader -> format | `format` | PASS (`v8`) |
| multi_05 | Test sự tập trung khi hỏi ngoài lề | `no_tool` (báo lỗi out_of_scope) | PASS (`v8`) |

Group evidence: `runs/v8_B_group_openai_20260729T165708460171.json`

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
