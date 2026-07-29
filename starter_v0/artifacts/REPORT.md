# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
>
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

| Thành viên        | MSSV        | Role                     | Nhiệm vụ chính                                                                                                                                                                                                           | Deliverable phụ trách                                                                             |
| ------------------- | ----------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Lê Hồ Quang Huy   | 2A202602026 | Tool Engineering Lead    | Thiết kế và triển khai ít nhất một tool mới; viết`TOOL.md`; đăng ký tool trong `tools/__init__.py` và `artifacts/tools.yaml`; smoke-test implementation và kiểm tra lỗi thực thi của các tool/API. | `tools/<new_tool>/`, tool registry, tool declaration và bằng chứng smoke test                  |
| Lã Phan Hoài An   | 2A202601846 | Eval & QA Lead           | Thiết kế đúng 10 team eval case gồm 5 single-turn và 5 multi-turn; kiểm tra schema/expected behavior; chạy regression và review thủ công các mismatch hoặc tool result có lỗi.                               | `data/eval_group.json`, kết quả group eval và QA evidence                                      |
| Nguyễn Tiến Đạt | 2A202601678 | Prompt & Evaluation Lead | Phân tích failed trace; tối ưu`system_prompt.md`/tool routing theo từng giả thuyết; chạy và so sánh `v0`–`v3`; quản lý metric, artifact hash và version history.                                        | `artifacts/system_prompt.md`, `artifacts/version_log.csv`, `runs/*.json` và failure analysis |
| Kiều Phúc Huy     | 2A202601056 | UI & Deployment Lead     | Xây dựng UI tái sử dụng agent loop trong`chat.py`; hiển thị request/response, tool trace, args, result/error và artifact version; lưu transcript; triển khai URL để nhóm khác kiểm thử.                   | `app.py`, UI dependencies, `transcripts/*.transcript.json` và public demo URL                  |
| Nguyễn Nam Phong   | 2A202601320 | Report & Demo Lead       | Tổng hợp evidence thật vào Report A/B; chuẩn bị 3–5 scenario demo, câu hỏi mẫu, fallback run/transcript; điều phối rehearsal, showdown và final submission checklist.                                         | `artifacts/REPORT.md`, demo script, rehearsal evidence và final gate                             |

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> Tìm paper, đọc nội dung và tóm tắt phương án/kết quả.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> URL: http://localhost:8501 (chạy `streamlit run app.py` trong `starter_v0/`)

## A2. Tool agent có

| Tên tool      | Làm được gì                                                                     | Tool mới nhóm thêm? |
| -------------- | ------------------------------------------------------------------------------------ | ---------------------- |
| clarify        | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận trước khi gửi | không                 |
| timeline       | Lấy tweet gần đây của một tài khoản cụ thể theo tên (Sam Altman→sama)    | không                 |
| fetch          | Đọc nội dung từ URL cụ thể                                                     | không                 |
| format         | Định dạng kết quả thành bản tin markdown                                      | không                 |
| lookup         | Tìm tin tức/thông tin trên web với timeframe và topic                          | không                 |
| paper_text     | Đọc nhanh một số trang đầu của paper                                          | không                 |
| papers         | Tìm paper trên arXiv theo chủ đề                                                | không                 |
| policy         | Tra quy định nội bộ về nghiên cứu, trích dẫn và quyền riêng tư          | không                 |
| send           | Gửi text lên Telegram (có confirmation guard)                                     | không                 |
| social_search  | Tìm tweet theo chủ đề, hỗ trợ Latest/Top                                       | không                 |
| paper_reader   | Đọc toàn bộ PDF, chia nội dung theo trang và section                           | Có                    |
| paper_sections | Trích riêng Method, Experiments, Results và Limitations cùng bằng chứng        | Có                    |
| explain_terms  | Giải thích thuật ngữ dựa trên ngữ cảnh trong paper và nguồn tham khảo     | Có                    |

## A3. Câu hỏi mẫu để thử

> 1. Tìm cho tôi các bài báo mới nhất về chủ đề RAG (Retrieval-Augmented Generation) trên arXiv.
> 2. Hãy tóm tắt cho tôi phần kết luận của bài báo đó.
> 3. Trích xuất phần Method và Results của bài báo mã 2310.11511.
> 4. Trong bài báo mã 1706.03762, tác giả định nghĩa thế nào về khái niệm 'Attention Mechanism'
> 5. Đọc lướt 2 trang đầu của bài báo 2401.00001 để tôi xem abstract.
> 6. Tìm bài báo về LoRA.
> 7. Tìm các bài báo nghiên cứu về Prompt Engineering.
> 8. Trích xuất phần Limitations của bài 2106.09685
> 9. Đọc toàn bộ bài 2310.11511.
> 10. Tìm paper về AI.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario              | Tool trace cần thấy | Câu chuyện cải thiện version    | Fallback run/transcript                    |
| --------------------- | --------------------- | ----------------------------------- | ------------------------------------------ |
| Tìm paper về LoRA   | v8                    | papers(topic="LoRA")                | transcripts/demo_search.transcript.json    |
| Đọc toàn bộ paper | v8                    | paper_reader(paper_id="2310.11511") | transcripts/demo_reader.transcript.json    |
| Trích xuất Method   | v8                    | paper_sections(section="Method")    | transcripts/demo_sections.transcript.jsons |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change                                | Hypothesis                                                                                                                        | Metric name   | Before | After | Run File                                         |
| ------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------- | -----: | ----: | ------------------------------------------------ |
| v0      | baseline                                          | Measure initial tool routing and argument behavior before optimization                                                            | case_accuracy |        |  0.65 | runs/v0_B_base_openai_20260729T145454761340.json |
| v1      | artifacts/system_prompt.md                        | Explicit scope clarification argument conventions and multi-tool routing will reduce the observed v0 mismatches                   | case_accuracy |   0.65 |  0.95 | runs/v1_B_base_openai_20260729T150524889742.json |
| v2      | artifacts/system_prompt.md                        | An initial external send request must trigger yes-no confirmation before a free-text clarification                                | case_accuracy |   0.95 |   1.0 | runs/v2_B_base_openai_20260729T150648551324.json |
| v3      | artifacts/system_prompt.md, artifacts/tools.yaml | General paper-tool boundaries and restored safety rules will preserve base routing while enabling the new capabilities            | case_accuracy |    1.0 |   0.9 | runs/v3_B_base_openai_20260729T163646947975.json |
| v4      | artifacts/system_prompt.md                        | Explicit clarification priority will recover R10 and R12 without changing other routes                                            | case_accuracy |    0.9 |  0.95 | runs/v4_B_base_openai_20260729T164718441470.json |
| v5      | artifacts/system_prompt.md                        | A top-level yes-no-only rule for initial external actions will recover R12 without regressing other routes                        | case_accuracy |   0.95 |   1.0 | runs/v5_B_base_openai_20260729T164822272536.json |
| v6      | artifacts/system_prompt.md                        | A no-repeat rule will stop equivalent paper tool calls without regressing the fixed base suite                                    | case_accuracy |    1.0 |   1.0 | runs/v6_B_base_openai_20260729T165127596562.json |
| v7      | artifacts/system_prompt.md                        | A pre-call deduplication rule will remove identical parallel calls while preserving fixed base accuracy                           | case_accuracy |    1.0 |   1.0 | runs/v7_B_base_openai_20260729T165351319485.json |
| v8      | artifacts/tools.yaml                              | An explicit single-call tool contract will prevent one duplicate call per requested paper category while preserving base accuracy | case_accuracy |    1.0 |   1.0 | runs/v8_B_base_openai_20260729T165541759790.json |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type            | Actual Tool Calls            | What Failed                                                                            | Fix                                                                                  |
| ------- | ----------------------- | ---------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| R10     | Missing clarification   | papers                       | Agent thực hiện tìm paper ngay khi người dùng chưa cung cấp đủ thông tin.   | Thêm quy tắc ưu tiên`clarify` trong `system_prompt.md`                       |
| R12     | Missing confirmation    | send                         | Agent thực hiện hành động gửi nội dung mà chưa xác nhận với người dùng. | Bổ sung quy tắc xác nhận Yes/No trước khi gọi`send`.                        |
| R17     | Duplicate tool call     | papers → papers             | Cùng một truy vấn nhưng tool bị gọi hai lần liên tiếp.                        | Thêm quy tắc chống duplicate trong`system_prompt.md`.                           |
| R19     | Duplicate paper reader  | paper_reader → paper_reader | Paper được đọc lại mặc dù đã có kết quả trước đó.                     | Thêm pre-call deduplication trước khi thực thi tool.                             |
| R21     | Incorrect tool boundary | paper_reader                 | Agent đọc toàn bộ paper trong khi chỉ cần đọc Abstract.                        | Điều chỉnh routing giữa`paper_text` và `paper_reader` trong `tools.yaml`. |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID   | What It Tests                                         | Expected Tool/Behavior               | Result        |
| --------- | ----------------------------------------------------- | ------------------------------------ | ------------- |
| single_01 | Tìm kiếm cơ bản với từ khóa                    | `papers`                           | PASS (`v8`) |
| single_02 | Bắt lỗi thiếu thông tin Paper ID                  | `clarify`                          | PASS (`v8`) |
| single_03 | Trích xuất chi tiết bằng tool mới paper_sections | `paper_sections`                   | PASS (`v8`) |
| single_04 | Giải thích chuyên sâu thuật ngữ trong paper     | `explain_terms`                    | PASS (`v8`) |
| single_05 | Phân biệt paper_text (đọc lướt) vs paper_reader | `paper_text`                       | PASS (`v8`) |
| multi_01  | Luồng papers -> paper_reader                         | `paper_reader`                     | PASS (`v8`) |
| multi_02  | Luồng papers -> paper_sections                       | `paper_sections`                   | PASS (`v8`) |
| multi_03  | Luồng paper_sections -> explain_terms                | `explain_terms`                    | PASS (`v8`) |
| multi_04  | Luồng paper_reader -> format                         | `format`                           | PASS (`v8`) |
| multi_05  | Test sự tập trung khi hỏi ngoài lề               | `no_tool` (báo lỗi out_of_scope) | PASS (`v8`) |

Group evidence: `runs/v8_B_group_openai_20260729T165708460171.json`

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn                                          | Version | Tool Calls + Args                               | Transcript/Run                              | Outcome                                                                                                                                                   |
| ------------------------------------------------------ | ------- | ----------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| User yêu cầu:**"tìm paper về xử lý ảnh"** | v2      | papers(query="image processing", max_results=5) | transcripts/v2_openai_20260729T161659732320 | Agent nhận diện đúng intent và gọi duy nhất một lần tool**papers** để tìm kiếm trên arXiv.                                            |
| Truy vấn arXiv                                        | v2      | api_query = all:image AND all:processing        | transcripts/v2_openai_20260729T161659732320 | Tool kết nối thành công với arXiv và tìm được**78.801** bài báo phù hợp với truy vấn.                                               |
| Trả kết quả tìm kiếm                              | v2      | papers → 5 results                             | transcripts/v2_openai_20260729T161659732320 | Trả về**5 bài báo** liên quan đến xử lý ảnh, mỗi bài gồm tiêu đề, tác giả, ngày xuất bản, tóm tắt, liên kết arXiv và PDF. |
| Tổng hợp phản hồi                                  | v2      | Không gọi thêm tool                          | transcripts/v2_openai_20260729T161659732320 | Agent tổng hợp kết quả thành danh sách dễ đọc và trình bày đầy đủ thông tin cho người dùng.                                           |
| Kết quả cuối cùng                                  | v2      | no_tool                                         | transcripts/v2_openai_20260729T161659732320 | Không phát sinh lỗi, không gọi lặp tool, routing chính xác và hoàn thành yêu cầu tìm kiếm paper thành công.                              |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category                              | Evidence File                | What Worked                                                                                                                                             | Risk / Guardrail                                                                                                                                                                |
| ------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Must-have: tool mới (paper_reader)   | tools/paper_reader.py        | Đọc và trích xuất nội dung từ PDF nghiên cứu, chuyển đổi thành văn bản để LLM xử lý.                                                 | Chất lượng phụ thuộc vào PDF (scan/image có thể OCR kém); cần giới hạn kích thước file và xử lý lỗi khi PDF không hợp lệ.                                 |
| Must-have: tool mới (explain_terms)  | tools/explain_terms.py       | Một số bài báo có cấu trúc không chuẩn nên việc nhận diện section có thể sai; cần fallback sang tìm kiếm theo tiêu đề gần đúng. | Có thể giải thích chưa chính xác với thuật ngữ chuyên ngành hiếm; nên yêu cầu LLM trả lời dựa trên nội dung bài báo và nêu rõ khi không chắc chắn. |
| Must-have: tool mới (paper_sections) | tools/paper_sections.py      | Tự động xác định các phần như Abstract, Introduction, Methodology, Results, Conclusion để hỗ trợ truy vấn theo từng mục.                | Một số bài báo có cấu trúc không chuẩn nên việc nhận diện section có thể sai; cần fallback sang tìm kiếm theo tiêu đề gần đúng.                         |
| Optional built-in (policy, papers)    | tools/policy/, tools/papers/ | Truy cập chính sách hoặc cơ sở dữ liệu bài báo thông qua built-in tool khi có API key hợp lệ.                                             | Cần cấu hình API key tương ứng để chạy thực tế; nếu thiếu key cần xử lý lỗi và thông báo rõ cho người dùng.                                             |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?

1. Làm rõ phạm vi của Research Agent chỉ xử lý các tác vụ liên quan đến paper nghiên cứu.
2. Bổ sung quy tắc ưu tiên `clarify` khi thiếu Paper ID hoặc thông tin truy vấn.
3. Thêm hướng dẫn lựa chọn đúng tool (`paper_text`, `paper_reader`, `paper_sections`) theo mục đích của người dùng.
4. Bổ sung quy tắc tránh gọi lặp cùng một tool cho cùng một yêu cầu.
5. Quy định phải xác nhận người dùng trước các hành động có ảnh hưởng bên ngoài (ví dụ `send`).

- Which fixes belonged in `tools.yaml`?

1. Khai báo ba custom tool: paper_reader, paper_sections, explain_terms.
2. Cập nhật mô tả (description) và input schema để agent hiểu rõ khi nào nên gọi từng tool.
3. Điều chỉnh routing nhằm phân biệt giữa đọc nhanh (`paper_text`) và đọc toàn bộ (`paper_reader`).
4. Thêm ràng buộc chỉ gọi mỗi tool một lần cho cùng một intent.

- Which failure needed manual review instead of automatic grading?

1. Chất lượng phần tóm tắt paper.
2. Độ chính xác của phần giải thích thuật ngữ.
3. Nội dung được trích xuất từ `paper_sections`.
4. Các câu trả lời yêu cầu suy luận hoặc tổng hợp từ nhiều section.

- What would you improve next?

1. Hỗ trợ thêm nguồn paper ngoài arXiv
2. Bổ sung citation theo từng đoạn văn được trích xuất.
3. Cải thiện khả năng nhận diện section trên nhiều định dạng PFD khác nhau.
4. tối ưu cache để tránh đọc lại cùng một PDF nhiều lần.

* Hỗ trợ thêm nguồn paper ngoài arXiv (Semantic Scholar, ACL Anthology, PubMed).
* Bổ sung citation theo từng đoạn văn được trích xuất.
* Cải thiện khả năng nhận diện section trên nhiều định dạng PDF khác nhau.
* Thêm chức năng so sánh nhiều paper theo Method, Dataset và Result.
* Tối ưu cache để tránh đọc lại cùng một PDF nhiều lần.
* Mở rộng bộ eval với nhiều tình huống multi-turn và edge case nhằm kiểm thử độ ổn định của agent.

* Hỗ trợ thêm nguồn paper ngoài arXiv (Semantic Scholar, ACL Anthology, PubMed).
* Bổ sung citation theo từng đoạn văn được trích xuất.
* Cải thiện khả năng nhận diện section trên nhiều định dạng PDF khác nhau.
* Thêm chức năng so sánh nhiều paper theo Method, Dataset và Result.
* Tối ưu cache để tránh đọc lại cùng một PDF nhiều lần.
* Mở rộng bộ eval với nhiều tình huống multi-turn và edge case nhằm kiểm thử độ ổn định của agent.

* Hỗ trợ thêm nguồn paper ngoài arXiv (Semantic Scholar, ACL Anthology, PubMed).
* Bổ sung citation theo từng đoạn văn được trích xuất.
* Cải thiện khả năng nhận diện section trên nhiều định dạng PDF khác nhau.
* Thêm chức năng so sánh nhiều paper theo Method, Dataset và Result.
* Tối ưu cache để tránh đọc lại cùng một PDF nhiều lần.
* Mở rộng bộ eval với nhiều tình huống multi-turn và edge case nhằm kiểm thử độ ổn định của agent.

* Hỗ trợ thêm nguồn paper ngoài arXiv (Semantic Scholar, ACL Anthology, PubMed).
* Bổ sung citation theo từng đoạn văn được trích xuất.
* Cải thiện khả năng nhận diện section trên nhiều định dạng PDF khác nhau.
* Thêm chức năng so sánh nhiều paper theo Method, Dataset và Result.
* Tối ưu cache để tránh đọc lại cùng một PDF nhiều lần.
* Mở rộng bộ eval với nhiều tình huống multi-turn và edge case nhằm kiểm thử độ ổn định của agent.
