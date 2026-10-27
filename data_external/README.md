# Dữ liệu ngoài

## population_34_provinces.csv
- **Nguồn:** danso.info – "Bảng dân số 34 tỉnh thành sau sáp nhập" (đăng 14/04/2025),
  https://danso.info/bang-dan-so-34-tinh-thanh-sau-sap-nhap/
- **Gốc số liệu:** Điều tra dân số và nhà ở giữa kỳ năm 2024 (Cục Thống kê – nso.gov.vn), cộng gộp theo
  phương án 34 tỉnh/thành (Nghị quyết 202/2025/QH15).
- **Kỳ dữ liệu:** năm 2024. **Phủ:** 34 tỉnh/thành, cấp tỉnh (không có cấp xã/phường).
- **Cách ghép:** khớp `province_std` của bảng `salesroom` (34/34 khớp tên).
- **Giới hạn:** tổng dân số (gồm cả trẻ em), không phải dân số trưởng thành có khả năng vay;
  là số liệu tổng hợp lại từ trang thứ cấp, chưa đối chiếu từng dòng với bản gốc của Cục Thống kê.

## income_2025_34_provinces.csv
- **Nội dung:** Thu nhập bình quân đầu người một tháng năm 2025 theo giá hiện hành, phân theo nguồn thu và địa phương
  (bảng 3). Đơn vị: **nghìn đồng/người/tháng**. Cột: tổng, tiền lương/tiền công, nông-lâm-thuỷ sản, phi nông nghiệp, nguồn khác.
- **Nguồn:** TODO – ghi tên tài liệu/đường dẫn gốc (nhiều khả năng Cục Thống kê, Khảo sát mức sống dân cư).
- **Kỳ dữ liệu:** năm 2025. **Phủ:** 34 tỉnh/thành, cấp tỉnh.
- **Kiểm tra:** tổng 4 nguồn = cột "Chung" (lệch tối đa 1 nghìn đồng do làm tròn); khớp 34/34 `province_std`.
- **Giới hạn:** thu nhập bình quân, không phản ánh phân phối thu nhập trong tỉnh; dân số (2024) và thu nhập (2025) lệch 1 năm.

## Cách dùng trong Addressable Market Ceiling (`05_Potential_Prioritization.ipynb`, Bước 6)
- **Mục đích (business relevance):** ước tính nhu cầu vay phù hợp mà công ty có thể phục vụ qua shop, theo địa bàn.
- **Cách ghép:** cấp tỉnh, khoá `province_std` (34 tỉnh sau sáp nhập, NQ 202/2025/QH15) – khớp 34/34 với `salesroom`; trần tỉnh chia cho shop theo năng lực cấu trúc (nhóm peer, chuỗi đại lý, tuổi đại lý, giá trị đơn hàng), không theo doanh số của chính shop.
- **Công thức:** Ceiling HĐ (tỉnh) = dân số × hồ sơ / 100K dân (mức các tỉnh tương đồng đã đạt) × tỷ lệ không bị từ chối × tỷ lệ hoàn tất sau duyệt.
  - "Mức các tỉnh tương đồng": hồi quy phân vị qua 34 tỉnh, log(hồ sơ / 100K dân) ~ log(thu nhập) + log(mật độ dân số); P75 = kịch bản thấp, P90 = kịch bản cơ sở; tỉnh đã cao hơn mức dự báo giữ mức thực tế.
  - Kịch bản cao = cơ sở ÷ 50% (giả định công ty đang nhận 50% nhu cầu trả góp tại đối tác; độ nhạy 30–70%).
- **Insight thêm:** hệ số co giãn theo thu nhập là 1,87 ở P75 và 0,91 ở P90 → thu nhập **không** làm nhu cầu vay tăng tỷ lệ thuận; vì vậy không nhân tuyến tính dân số × thu nhập.
- **Giả định, giới hạn, thiên lệch:** chỉ 34 điểm quan sát (khoảng rộng); dân số tổng (chưa tách độ tuổi trưởng thành); thu nhập bình quân không phản ánh phân phối; dân số 2024 và thu nhập 2025 lệch 1 năm; cấp tỉnh rộng hơn vùng phục vụ thật của shop (chưa có nơi ở của khách); chưa có dữ liệu giao dịch của đối tác và đối thủ.
