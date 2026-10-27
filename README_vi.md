# BI10 Round 3 – How big can this shop become?

Câu hỏi trung tâm của đề: *"How far can a specific shop realistically grow, what constrains its growth, and what should Sales Management do to close the opportunity gap?"*

Bài đi theo **một mạch duy nhất**, mỗi file trả lời một phần của đề và đưa kết quả cho file sau:

```
Round3_BI10_dataset/ ─► 01_EDA ─► 02_clean_data ─► data_clean/ ─┬─► 03_Current_Actual  (shop đang đạt gì?)
data_external/ (dân số, thu nhập 34 tỉnh) ───────────────────────┤
                                                                  ├─► 04_BAU ─► output/bau_2026Q4.csv
                                                                  │                    │
                                                                  └────────────────────┴─► 05_Potential_Prioritization
                                                                                              (Attainable · Ceiling · 2 shop cùng doanh số ·
                                                                                               ưu tiên · kiểm chứng · tổng hợp trả lời đề)
```

| File | Vai trò | Đầu ra |
|---|---|---|
| `01_EDA.ipynb` | Hiểu dữ liệu: null, trùng, outlier, khoá nối, quy tắc nối lead → hợp đồng | Quy tắc làm sạch |
| `02_clean_data.py` | Làm sạch, chuẩn hoá 34 tỉnh sau sáp nhập, nối lead → hợp đồng theo luật của đề | `data_clean/*.csv`, `cleaning_log.csv` |
| `02b_Overview_Market_Customer_Lead_SA.ipynb` | Bối cảnh: thị trường, chân dung & hành vi khách hàng (Round 2), hệ thống lead, đội ngũ SA | biểu đồ bối cảnh |
| `03_Current_Actual.ipynb` | **Current Actual** và bức tranh kinh doanh theo phân khúc | `output/hien_trang_*.csv` |
| `04_BAU.ipynb` | **Business-as-Usual**: dự báo quý tới, backtest, khoảng bất định, giải thích mô hình | `output/bau_2026Q4.csv` |
| `05_Potential_Prioritization.ipynb` | **Attainable**, **Ceiling**, khoảng cách và nguyên nhân, ưu tiên nguồn lực, kiểm chứng, **tổng hợp trả lời đề** | `output/shop_potential_2026Q3.csv`, `output/tra_loi_de_bai.csv` |
| `data_external/README.md` | 5 điểm bắt buộc cho từng bộ dữ liệu ngoài | |

**Thứ tự chạy:** `python 02_clean_data.py` → `02b` → `03` → `04` → `05` (05 đọc kết quả của 04). Chạy mọi file từ thư mục này.

---

## Câu hỏi của đề → trả lời ở đâu

| Câu hỏi / yêu cầu của đề | File · mục |
|---|---|
| **Current Actual** – what the shop is achieving today | `03` mục 1, 6, 7, 10 · tóm tắt ở `05` Bước 3 |
| **Business-as-Usual** – if current conditions and trends continue | `04` (Bước 1–5, mục "Trả lời") · dùng ở `05` Bước 4 |
| **Attainable Potential** – with feasible interventions | `05` Bước 5 |
| **Addressable Market Ceiling** – market that could theoretically be served | `05` Bước 6 |
| Four concepts not used interchangeably | `05` Bước 1 (mỗi mức một cột, kiểm tra BAU ≤ Attainable ≤ Ceiling) |
| *If two shops have similar current sales, which one has room to grow?* | `05` Bước 7 (ví dụ 2 shop thật) · `04` Bước 5 (2 shop cùng doanh số, BAU khác) |
| What data and KPIs are needed | `03` mục 0–1 · `05` Bước 1–2 |
| How current performance and future trajectory should be assessed | `03` mục 3 (xu hướng, tăng trưởng, vòng đời) · `04` |
| How realistic growth potential should be estimated | `05` Bước 5 (biện pháp → tác động đo được → kết quả) |
| What factors create or constrain the gap (demand, execution, staffing, merchant, product mix, risk) | `03` mục 4, 7, 8, 9 (theo phân khúc) · `05` Bước 5, 7 (theo shop) |
| How to prioritize shops when resources are limited | `05` Bước 8 |
| Reliability and uncertainty of the estimates | `04` Bước 3–4 (backtest, P10–P90) · `05` Bước 9 (độ nhạy, bootstrap) |
| How recommendations could be validated in practice | `05` Bước 9 (backtest dư địa, cỡ mẫu pilot) |
| Cross-sell from physical shop to online | `03` mục 5.2, 8.2 (phễu lead theo shop gốc, tách HĐ trực tiếp vs bán chéo) · `05` Bước 3 (góc Origination), Bước 5 (đòn bẩy bán chéo) |
| External data (5 điểm bắt buộc) | `data_external/README.md` · `05` Bước 6 |
| Storyline nối Round 2 | `05` Bước 2 (nhãn khách Round 2) |

---

## Công cụ và phương pháp theo từng bước

| Bước | Kỹ thuật | Công cụ | Vì sao phù hợp |
|---|---|---|---|
| Dữ liệu (01, 02) | Kiểm tra null / trùng / outlier; null trá hình → NULL + cờ; chuẩn hoá 34 tỉnh; nối lead → hợp đồng theo 3 tiêu chí của đề, ghép 1-1 trong 30 ngày | DuckDB SQL, pandas | Dữ liệu hàng triệu dòng; SQL dễ đối chiếu với quy tắc của đề |
| Current Actual (03) | KPI theo phễu (hồ sơ → duyệt → ký), tách tăng trưởng mạng lưới vs năng suất, phân khúc dòng hàng × mô hình, vòng đời shop | DuckDB SQL, pandas, matplotlib | Mô tả minh bạch, cùng định nghĩa với các bước sau |
| BAU (04) | So 17 phương pháp bằng backtest 3 mốc; chọn M12 (trung bình LightGBM, Random Forest, làm mượt luỹ thừa) theo sai số và độ lệch theo nhóm shop; P10–P90 từ sai số backtest; Monte Carlo; giá trị Shapley theo nhóm yếu tố; khoản vay bình quân có xu hướng (backtest) | LightGBM, scikit-learn | Chọn bằng kiểm định ngoài thời gian, không theo độ phức tạp; Shapley để giải thích được cho người không chuyên |
| Attainable (05 Bước 5) | Danh mục biện pháp trong thẩm quyền bán hàng; tác động lead / SA đo bằng thay đổi trong cùng shop giữa 2 quý (đã trừ biến động chung); tỷ lệ đóng khoảng cách trong lịch sử; tính lại phễu; chặn rủi ro FPD > P90 peer | pandas, numpy | Mỗi mức tiềm năng gắn với một biện pháp và bằng chứng; P75 peer chỉ là tham chiếu |
| Ceiling (05 Bước 6) | Chuỗi tỷ lệ có điều kiện: dân số × nhu cầu / người × đáp ứng điều kiện × hoàn tất; hồi quy phân vị qua 34 tỉnh; kịch bản thấp / cơ sở / cao | scikit-learn (QuantileRegressor) | Đo quan hệ thu nhập – nhu cầu thay vì giả định tỷ lệ thuận; giả định công khai |
| Ưu tiên (05 Bước 8) | Giá trị tăng thêm × (1 − FPD) khai thác được trong 6 tháng; tầng A–D; đường "ngân sách cho N shop" | pandas | Xếp theo giá trị đã điều chỉnh rủi ro, đúng cách quản lý bán hàng phân bổ nguồn lực |
| Kiểm chứng (04, 05 Bước 9) | Backtest ngoài thời gian (shop "dư địa lớn" có tăng nhanh hơn không), độ nhạy P70/P80, bootstrap, cỡ mẫu pilot | scipy, numpy | Đo độ tin cậy của con số và cách kiểm chứng ngoài thực tế |

---

## Quy ước chung
- Đơn vị: **shop vật lý** · chỉ số chính **HĐ ký thành công / tháng**, báo cáo song song **giá trị khoản vay đã ký** (điều chỉnh rủi ro: × (1 − FPD)).
- Hiện tại = **Q3/2026** · dự báo = **Q4/2026**.
- Biến dùng để chia nhóm và tính trần chỉ là đặc điểm shop / đại lý / thị trường, **không dùng kết quả bán của chính shop**.
- Mỗi HĐ chỉ tính **một lần** trong tổng mạng lưới (HĐ online có lead từ shop được chuyển về shop đó).

