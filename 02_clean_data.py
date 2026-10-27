"""
BI10 Round 3 - Bước 2/5 · Làm sạch dữ liệu (đọc tiếp: 03_Current_Actual.ipynb; bản đồ toàn bài: README.md)
Input : Round3_BI10_dataset/  (raw, không sửa)
Output: data_clean/*.csv  + data_clean/cleaning_log.csv

Nguyên tắc:
- Không xoá dòng trừ khi trùng y hệt. Giá trị sai -> NULL + cột flag_* để còn truy vết.
- Null trá hình (XNA, '.', -1, 3000-01-01, credit_amount=0 ở CC/BNPL) -> NULL thật.
- Region: chuẩn hoá tên tỉnh về 34 tỉnh sau sáp nhập 01/07/2025 (province_std).
Chạy:  python 02_clean_data.py

Mã sản phẩm (contract.product, leads.code_product_type) – suy từ dữ liệu, StructureTable không ghi tên đầy đủ:
  CD   Consumer Durables – trả góp hàng tiêu dùng (điện thoại, làm đẹp, thể thao, điện máy, nội thất…).
       Có price; price - init_pay = credit_amount; vay trung vị 9M, 6 kỳ (4–36), trả trước ~30%.
  TW   Two Wheelers – trả góp xe máy. Có price; vay trung vị ~20M, 12 kỳ, trả trước ~30%.
  CL   Cash Loan – vay tiền mặt, không gắn món hàng: price NULL, init_pay = 0; 5M–250M, 3–60 kỳ.
       Mã gốc ở leads: SCC, PRC, CLX, CEL, SCC PR2/PR3 (CLX = lead nhập tay từ WDE/GMA/CRM).
  CW   Vay tiền mặt dạng khác (không giá hàng, init_pay = 0, 3M–50M, ≤ 36 kỳ); dữ liệu không ghi tên.
  CC   Credit Card – thẻ tín dụng: chỉ có hạn mức, credit_amount = 0, quy mô đo bằng amt_billing_*.
  BNPL Buy Now Pay Later – mua trước trả sau, khoản nhỏ; 71% credit_amount = 0 -> dùng amt_billing_1st.
  REL  Chỉ có ở leads (không có HĐ REL); link hệ thống cho thấy REL -> CC nên ghép như CC.
Dòng hàng của shop (salesroom_product): CD, TW, NS (dòng khác; brand bắt đầu 'RL' xếp vào NS).
"""
import os, re, unicodedata
import duckdb, pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "Round3_BI10_dataset").replace("\\", "/") + "/"
OUT = os.path.join(BASE, "data_clean").replace("\\", "/") + "/"
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()
log = []

def note(table, step, before, after, detail=""):
    log.append(dict(table=table, step=step, rows_before=before, rows_after=after, affected=before - after if before != after else None, detail=detail))
    print(f"[{table}] {step}: {before:,} -> {after:,} {detail}")

def n(sql):
    return con.execute(sql).fetchone()[0]

# ---------------------------------------------------------------- REGION MAP
# Tỉnh cũ -> tỉnh mới (Nghị quyết 202/2025/QH15, hiệu lực 01/07/2025)
PROVINCE_MAP = {
    "Hà Giang": "Tuyên Quang", "Yên Bái": "Lào Cai", "Bắc Kạn": "Thái Nguyên",
    "Vĩnh Phúc": "Phú Thọ", "Hòa Bình": "Phú Thọ", "Bắc Giang": "Bắc Ninh",
    "Thái Bình": "Hưng Yên", "Hải Dương": "Hải Phòng", "Hà Nam": "Ninh Bình",
    "Nam Định": "Ninh Bình", "Quảng Bình": "Quảng Trị", "Quảng Nam": "Đà Nẵng",
    "Kon Tum": "Quảng Ngãi", "Bình Định": "Gia Lai", "Ninh Thuận": "Khánh Hòa",
    "Phú Yên": "Đắk Lắk", "Đắk Nông": "Lâm Đồng", "Bình Thuận": "Lâm Đồng",
    "Bình Phước": "Đồng Nai", "Bình Dương": "TP. Hồ Chí Minh", "Bà Rịa - Vũng Tàu": "TP. Hồ Chí Minh",
    "Long An": "Tây Ninh", "Tiền Giang": "Đồng Tháp", "Bến Tre": "Vĩnh Long",
    "Trà Vinh": "Vĩnh Long", "Sóc Trăng": "Cần Thơ", "Hậu Giang": "Cần Thơ",
    "Bạc Liêu": "Cà Mau", "Kiên Giang": "An Giang",
    # đồng nhất cách viết thành phố
    "TP.HCM": "TP. Hồ Chí Minh", "TP. Hà Nội": "Hà Nội", "TP. Huế": "Huế",
    "TP. Đồng Nai": "Đồng Nai", "Hải Phòng": "Hải Phòng", "Cần Thơ": "Cần Thơ", "Đà Nẵng": "Đà Nẵng",
}

def nfc(s):
    return unicodedata.normalize("NFC", s.strip()) if isinstance(s, str) else s

def std_province(p):
    p = nfc(p)
    return PROVINCE_MAP.get(p, p) if isinstance(p, str) else p

def std_town(t):
    """'PHƯỜNG YÊN  HÒA' / 'P. Yên Hòa' -> 'Phường Yên Hòa'; '.'/'-' -> NULL"""
    if not isinstance(t, str):
        return None
    t = re.sub(r"\s+", " ", nfc(t))
    if t in {".", "-", "", "XNA"}:
        return None
    t = t.title()
    t = re.sub(r"^P\.\s*", "Phường ", t)
    t = re.sub(r"^X\.\s*", "Xã ", t)
    t = re.sub(r"^Tt\.?\s*", "Thị Trấn ", t)
    return t

def parse_dt(s):
    return pd.to_datetime(s, format="%d-%m-%Y %H:%M:%S", errors="coerce")

# ---------------------------------------------------------------- SALESROOM
sr = pd.read_excel(RAW + "salesroom.xlsx")
b = len(sr); sr = sr.drop_duplicates(); note("salesroom", "drop exact dup", b, len(sr))
sr.columns = [c.lower() for c in sr.columns]
sr["salesroom_start"] = parse_dt(sr.salesroom_start)
sr["salesroom_end"] = parse_dt(sr.salesroom_end)
# StructureTable: district '.' = địa giới MỚI (bỏ cấp huyện, NQ 202/2025/QH15), khác '.' = địa giới cũ
sr["is_new_boundary"] = sr.salesroom_district.map(nfc).eq(".")
sr["salesroom_district"] = sr.salesroom_district.map(lambda x: None if nfc(x) in {".", "-", ""} else nfc(x))
sr["salesroom_town_raw"] = sr.salesroom_town
sr["salesroom_town"] = sr.salesroom_town.map(std_town)
sr["salesroom_province_raw"] = sr.salesroom_province
sr["province_std"] = sr.salesroom_province.map(std_province)
sr["flag_old_province_name"] = sr.salesroom_province.map(nfc).isin(
    [k for k in PROVINCE_MAP if not k.startswith("TP")] ) & (sr.province_std != sr.salesroom_province.map(nfc))
sr["is_closed"] = sr.salesroom_status.eq("Closed")
note("salesroom", "district '.' (new boundary) -> NULL + is_new_boundary", len(sr), len(sr), f"{sr.is_new_boundary.sum():,} new / {sr.salesroom_district.isna().sum():,} NULL")
note("salesroom", "old province name mapped", len(sr), len(sr), f"{sr.flag_old_province_name.sum():,} shops")

# ---------------------------------------------------------------- SELLER
se = pd.read_excel(RAW + "seller.xlsx")
b = len(se); se = se.drop_duplicates(); note("seller", "drop exact dup", b, len(se))
se.columns = [c.lower() for c in se.columns]
se["seller_active_date"] = parse_dt(se.seller_active_date)
se["seller_province_std"] = se.seller_province.map(std_province)

# vùng của shop lấy theo SHOP (seller province thường là trụ sở HCM/HN)
sr = sr.merge(se[["skp_seller", "seller_province_std", "seller_type", "seller_status"]], on="skp_seller", how="left")
sr["flag_seller_missing"] = sr.seller_province_std.isna()
sr["flag_province_ne_seller"] = (~sr.flag_seller_missing) & (sr.province_std != sr.seller_province_std)
note("salesroom", "flag province != seller province", len(sr), len(sr), f"{sr.flag_province_ne_seller.sum():,} shops")
note("salesroom", "flag seller missing", len(sr), len(sr), f"{sr.flag_seller_missing.sum():,} shops")

sr.to_csv(OUT + "salesroom.csv", index=False, encoding="utf-8-sig")
se.to_csv(OUT + "seller.csv", index=False, encoding="utf-8-sig")
con.register("sr", sr)

# ---------------------------------------------------------------- CONTRACT
# Kiểm tra 5 biến tiền / kỳ hạn trên dữ liệu gốc (3.775.371 HĐ):
#   price         chỉ có ở CD/TW; min CD 1M, TW 5M, max 265M; không 0/âm. 827 HĐ CD > 100M (trả trước ~50%) -> hợp lý, giữ
#   init_pay      CL/CW/CC/BNPL luôn 0 (đúng nghiệp vụ). CD/TW: 37K HĐ = 0 (chương trình 0%) -> giữ;
#                 ~100 HĐ trả trước tượng trưng 1.000đ – < 100K -> flag_init_pay_token
#   credit_amount 1 HĐ BNPL = 1đ -> NULL; CC 100% = 0 và BNPL 71% = 0 (hạn mức, không giải ngân) -> NULL;
#                 product NULL (Rejected/Cancelled) luôn = 0 -> NULL; sàn theo chính sách: CD 1M, TW 5M, CW 3M, CL 5M
#   ins_amount    không âm, không > credit_amount; 1.179 dòng lẻ thập phân (phí tính theo %) -> giữ;
#                 phí > 30% khoản vay (CL tối đa 71% ở 57 kỳ) -> flag_ins_ratio_high
#   payment_num   3–60 kỳ, không 0/âm; CL > 57 kỳ (trần kỳ hạn ở leads) và CW > 36 kỳ -> flag_tenor_unusual
#   ràng buộc     CD/TW: price - init_pay = credit_amount khớp 100%; không có init_pay > price hay credit_amount > price
con.execute(f"create table c_raw as select * from read_csv('{RAW}contract.csv')")
b = n("select count(*) from c_raw")
con.execute("create table c0 as select distinct * from c_raw")
note("contract", "drop exact dup", b, n("select count(*) from c0"))

con.execute("""
create table contract as
select
  skp_salesroom, skp_credit_case,
  skp_emp_pre_process::BIGINT           as skp_emp_pre_process,
  skp_product::BIGINT                   as skp_product,
  coalesce(product, 'UNKNOWN')          as product,
  name_status,
  -- tiền
  price, init_pay,
  case when credit_amount = 0 and product in ('CC','BNPL') then NULL     -- null trá hình
       when credit_amount < 100000 then NULL                             -- placeholder (=1 VND)
       when product is null then NULL
       else credit_amount end            as credit_amount,
  ins_amount,
  payment_num::INT                       as payment_num,
  skp_client::BIGINT                     as skp_client,
  -- ngày
  date_apply,
  case when year(date_sign) = 3000 then NULL else date_sign end as date_sign,
  year(date_sign) < 3000                 as is_signed,
  -- billing: chỉ có nghĩa với CC/BNPL; 0 = chưa phát sinh
  case when product in ('CC','BNPL') then nullif(amt_billing_1st,0) end as amt_billing_1st,
  case when product in ('CC','BNPL') then nullif(amt_billing_2nd,0) end as amt_billing_2nd,
  case when product in ('CC','BNPL') then nullif(amt_billing_3rd,0) end as amt_billing_3rd,
  -- dpd là cờ 0/1, không phải số ngày
  dpd_1pd::INT as flag_dpd_1pd, dpd_2pd::INT as flag_dpd_2pd,
  dpd_3pd::INT as flag_dpd_3pd, dpd_4pd::INT as flag_dpd_4pd,
  greatest(dpd_1pd, dpd_2pd, dpd_3pd, dpd_4pd)::INT as flag_any_dpd,
  -- flags
  product is null                                                   as flag_product_missing,
  credit_amount > 0 and credit_amount < 100000                      as flag_credit_placeholder,
  name_status in ('Cancelled','Rejected') and year(date_sign) < 3000 as flag_status_conflict,
  product in ('CC','BNPL') and amt_billing_1st > 100e6              as flag_billing_outlier,
  product = 'BNPL' and coalesce(credit_amount,0) = 0 and amt_billing_1st > 0 as flag_bnpl_credit_from_billing,
  product in ('CD','TW') and init_pay > 0 and init_pay < 100000     as flag_init_pay_token,
  coalesce(ins_amount > 0.3 * credit_amount and credit_amount > 0, false) as flag_ins_ratio_high,
  coalesce((product = 'CL' and payment_num > 57) or (product = 'CW' and payment_num > 36), false) as flag_tenor_unusual,
  skp_salesroom in (select skp_salesroom from sr)                   as in_scope_new_shop
from c0
""")
# Giá trị khoản vay dùng phân tích: CL/CW/CD/TW = credit_amount; BNPL thiếu -> billing kỳ 1; CC không có hạn mức -> NULL
con.execute("""alter table contract add column loan_amount_eff DOUBLE;
update contract set loan_amount_eff = case when product='BNPL' then coalesce(credit_amount, amt_billing_1st)
                                           when product='CC' then NULL else credit_amount end""")
N = n("select count(*) from contract")
for col, label in [("flag_product_missing", "product NULL -> 'UNKNOWN'"),
                   ("flag_credit_placeholder", "credit_amount < 100K -> NULL"),
                   ("flag_status_conflict", "Cancelled/Rejected but signed"),
                   ("flag_billing_outlier", "billing 1st > 100M (flag)"),
                   ("flag_bnpl_credit_from_billing", "BNPL credit=0 -> loan_amount_eff from billing"),
                   ("flag_init_pay_token", "CD/TW init_pay 0 < x < 100K (flag)"),
                   ("flag_ins_ratio_high", "ins_amount > 30% credit_amount (flag)"),
                   ("flag_tenor_unusual", "CL > 57 kỳ / CW > 36 kỳ (flag)"),
                   ("not is_signed", "date_sign 3000 -> NULL")]:
    note("contract", label, N, N, f"{n(f'select count(*) from contract where {col}'):,} rows")
cc_null = n("select count(*) from contract where product in ('CC','BNPL') and credit_amount is null")
note("contract", "CC/BNPL credit_amount 0 -> NULL", N, N, f"{cc_null:,} rows")
con.execute(f"copy contract to '{OUT}contract.csv' (format csv, header)")

# ---------------------------------------------------------------- CONTRACT_PRODUCT
con.execute(f"create table cp_raw as select * from read_csv('{RAW}contract_product.csv')")
b = n("select count(*) from cp_raw")
con.execute("""
create table cp1 as
select distinct skp_credit_case,
  upper(trim(name_producer))                                  as name_producer,
  replace(upper(trim(name_goods_category)), 'WEELERS', 'WHEELERS') as name_goods_category,
  replace(upper(trim(name_goods_type)), 'WEELERS', 'WHEELERS')     as name_goods_type,
  -- gộp nhãn trùng nghĩa còn sót sau upper()
  case upper(trim(goods_group)) when 'FURNITURE & MATTRESSES' then 'FURNITURE'
       when 'OTHER' then 'OTHERS' else upper(trim(goods_group)) end as goods_group
from cp_raw""")
note("contract_product", "normalize case/typo + drop exact dup", b, n("select count(*) from cp1"))
# goods_group NULL -> group phổ biến nhất của cùng category
con.execute("""
create table contract_product as
with m as (select name_goods_category, arg_max(goods_group, cnt) g
           from (select name_goods_category, goods_group, count(*) cnt from cp1 where goods_group is not null group by all)
           group by 1)
select cp1.* exclude (goods_group),
       coalesce(cp1.goods_group, m.g) as goods_group,
       cp1.goods_group is null        as flag_goods_group_imputed,
       count(*) over (partition by skp_credit_case) as n_items
from cp1 left join m using (name_goods_category)""")
N = n("select count(*) from contract_product")
note("contract_product", "goods_group NULL imputed from category", N, N,
     f"{n('select count(*) from contract_product where flag_goods_group_imputed'):,} rows")
con.execute(f"copy contract_product to '{OUT}contract_product.csv' (format csv, header)")

# ---------------------------------------------------------------- LEADS
con.execute(f"""create table l_raw as select * from read_csv('{RAW}leads.csv',
  types={{'code_pos':'VARCHAR','code_sa':'VARCHAR','text_tenor':'VARCHAR','text_contract_number':'VARCHAR','text_accepted_by':'VARCHAR'}})""")
b = n("select count(*) from l_raw")
con.execute("create table l0 as select distinct * from l_raw")
note("leads", "drop exact dup", b, n("select count(*) from l0"),
     "(id_uuid trùng KHÔNG xoá: 1 uuid = 1 phiên khách nhận nhiều offer)")

# amt_loan_limit (dữ liệu gốc):
#   sạch   : không âm / 0; trần đúng chính sách CD ≤ 60M, TW ≤ 80M, CC ≤ 80M, REL ≤ 50M, sàn 5M (CD 1M);
#            CD/TW/CC/REL tròn 100K; cùng (uuid, sản phẩm) hạn mức không đổi; ~19K null thật (CC/CD/TW).
#   bất thường – chỉ ở CL mã gốc CLX (WDE/GMA/CRM, hạn mức nhập tay; INSTANT do hệ thống đặt nên tròn):
#     1 dòng = 9đ (HĐ thực vay 9M, sai đơn vị) · 7 dòng 4,6–19 tỷ (nhập nhầm trường) · 2 dòng 340M/800M
#     153 dòng 250–281M (≈ 250M + phí bảo hiểm, nhiều khả năng hợp lệ) · ~11K giá trị lẻ 1đ (50.000.001…, giữ)
#     75 / 62K link hệ thống có khoản vay > hạn mức (lỗi ×10)
# xử lý: < 1M hoặc CL > 300M -> NULL (10 dòng sai); CL 250–300M giữ giá trị + flag_limit_above_cap
# trần hạn mức theo sản phẩm (max hợp lệ quan sát được / policy)
con.execute("""
create table leads as
select
  row_number() over (order by id_uuid, code_product_type, dtime_created, date_assigned) as lead_id,
  id_uuid, dtime_created, date_assigned, id_lead_source,
  -- WDE/GMA/CRM: lead sinh SAU khi khách đã nộp hồ sơ (97-100% link hệ thống) -> lead chăm sóc hồ sơ có sẵn
  case when id_lead_source in ('WDE','GMA','GMA_BIG_TICKET','CRM') then 'FOLLOW_UP' else 'ORIGINATION' end as lead_flow,
  nullif(text_accepted_by, 'XNA')                as text_accepted_by,
  case when amt_loan_limit < 1e6 then NULL
       when code_product_type = 'CL' and amt_loan_limit > 300e6 then NULL
       else amt_loan_limit end                    as amt_loan_limit,
  nullif(code_pos, 'XNA')                         as code_pos,
  skp_salesroom, code_lead_status,
  nullif(text_contract_number, 'XNA')             as text_contract_number,
  nullif(try_cast(nullif(text_tenor,'XNA') as INT), 0) as tenor,
  nullif(code_sa, 'XNA')                          as code_sa,
  result::INT                                     as result,
  nullif(skp_credit_case, -1)                     as skp_credit_case,
  skp_client, sample_weight,
  code_product_type_original, code_product_type,
  -- flags
  amt_loan_limit < 1e6 or (code_product_type='CL' and amt_loan_limit > 300e6) as flag_loan_limit_outlier,
  coalesce(code_product_type = 'CL' and amt_loan_limit > 250e6 and amt_loan_limit <= 300e6, false) as flag_limit_above_cap,
  -- mô tả lỗi dữ liệu hạn mức (không sửa giá trị; giá trị gốc của dòng bị NULL giữ ở amt_loan_limit_raw)
  case when amt_loan_limit < 1e6 then 'Sai đơn vị: < 1M (vd 9đ, HĐ liên kết vay 9M)'
       when code_product_type = 'CL' and amt_loan_limit > 1e9 then 'Giá trị rác: > 1 tỷ (4,6–19 tỷ, nhập nhầm trường)'
       when code_product_type = 'CL' and amt_loan_limit > 300e6 then 'Thừa chữ số: 300M–1 tỷ (HĐ liên kết vay 40M/80M)'
       when code_product_type = 'CL' and amt_loan_limit > 250e6 then 'Vượt trần CL 250M (≈ 250M + phí bảo hiểm, giữ)'
  end                                             as limit_issue,
  case when amt_loan_limit < 1e6 or (code_product_type = 'CL' and amt_loan_limit > 300e6) then amt_loan_limit end as amt_loan_limit_raw,
  date_assigned < dtime_created                   as flag_assign_before_create,
  skp_salesroom in (select skp_salesroom from sr) as in_scope_new_shop,
  -- tháng/tuần tiện cho EDA
  date_trunc('week', date_assigned)::DATE         as week_assigned
from l0""")  # skp_employee bỏ: 100% NULL
N = n("select count(*) from leads")
for col, label in [("flag_loan_limit_outlier", "amt_loan_limit <1M or CL >300M -> NULL"),
                   ("flag_limit_above_cap", "CL amt_loan_limit 250–300M (giữ, flag)"),
                   ("flag_assign_before_create", "date_assigned < dtime_created (flag)"),
                   ("tenor is null", "tenor XNA/0 -> NULL"),
                   ("skp_credit_case is null", "skp_credit_case -1 -> NULL")]:
    note("leads", label, N, N, f"{n(f'select count(*) from leads where {col}'):,} rows")
for issue_, cnt in con.execute("select limit_issue, count(*) from leads where limit_issue is not null group by 1 order by 2").fetchall():
    note("leads", f"amt_loan_limit – {issue_}", N, N, f"{cnt:,} rows")
note("leads", "drop skp_employee (100% NULL)", N, N)

# ---------------------------------------------------------------- LEAD -> CONTRACT LINK
# Lead gắn với hợp đồng khi: cùng skp_client + cùng sản phẩm + giao lead trước mốc thời gian, trong LINK_DAYS ngày.
# Hai hướng, mỗi hướng ghép 1-1 riêng:
#   match_apply : date_assigned <= date_apply  -> lead TẠO RA hồ sơ mới   (hợp lý cho lead_flow = ORIGINATION)
#   match_sign  : date_assigned <= date_sign   -> lead GIÚP ra hợp đồng ký (áp dụng cả FOLLOW_UP)
# 1-1: mỗi hợp đồng lấy lead giao gần nhất trước nó (last touch), rồi mỗi lead giữ hợp đồng gần nhất.
#      Link hệ thống (leads.skp_credit_case) được ưu tiên khi xếp hạng.
# REL ghép như CC (contract không có REL; 821 link hệ thống REL -> CC).
LINK_DAYS = 30
con.execute(f"""
create table link_cand as
select l.lead_id, l.id_uuid, l.code_product_type, l.id_lead_source, l.lead_flow, l.date_assigned,
       c.skp_credit_case, c.product, c.date_apply, c.date_sign, c.is_signed, c.name_status,
       coalesce(l.skp_credit_case = c.skp_credit_case, false) as is_system_link,
       l.date_assigned <= c.date_apply and c.date_apply <= l.date_assigned + interval {LINK_DAYS} day as ok_apply,
       coalesce(c.is_signed and l.date_assigned <= c.date_sign
                and c.date_sign <= l.date_assigned + interval {LINK_DAYS} day, false) as ok_sign
from leads l join contract c
  on c.skp_client = l.skp_client
 and c.product = case when l.code_product_type = 'REL' then 'CC' else l.code_product_type end
where l.skp_client > 0
  and ((l.date_assigned <= c.date_apply and c.date_apply <= l.date_assigned + interval {LINK_DAYS} day)
    or (c.is_signed and l.date_assigned <= c.date_sign and c.date_sign <= l.date_assigned + interval {LINK_DAYS} day)
    or l.skp_credit_case = c.skp_credit_case)""")

def one_to_one(ok, t):
    return f"""
    select lead_id, skp_credit_case from (
      select *, row_number() over (partition by lead_id order by is_system_link desc, {t}) r2 from (
        select *, row_number() over (partition by skp_credit_case order by is_system_link desc, date_assigned desc, lead_id desc) r1
        from link_cand where {ok}) where r1 = 1) where r2 = 1"""

con.execute(f"""
create table lead_contract_link as
select k.*,
       date_diff('minute', k.date_assigned, k.date_apply) / 60.0 as hrs_assign_to_apply,
       date_diff('minute', k.date_assigned, k.date_sign)  / 60.0 as hrs_assign_to_sign,
       a.lead_id is not null as match_apply,
       s.lead_id is not null as match_sign
from link_cand k
left join ({one_to_one('ok_apply', 'date_apply')}) a using (lead_id, skp_credit_case)
left join ({one_to_one('ok_sign', 'date_sign')}) s using (lead_id, skp_credit_case)
where a.lead_id is not null or s.lead_id is not null""")
N = n("select count(*) from lead_contract_link")
for col, label in [("match_apply", f"lead -> hồ sơ (assigned <= apply, {LINK_DAYS}d, 1-1)"),
                   ("match_sign", f"lead -> hợp đồng ký (assigned <= sign, {LINK_DAYS}d, 1-1)"),
                   ("is_system_link", "trùng leads.skp_credit_case")]:
    note("lead_contract_link", label, N, N, f"{n(f'select count(*) from lead_contract_link where {col}'):,} rows")
con.execute(f"copy lead_contract_link to '{OUT}lead_contract_link.csv' (format csv, header)")

# cờ chuyển đổi trên từng lead (để tính tỷ lệ trực tiếp)
con.execute("""
create or replace table leads as
select l.*, coalesce(k.converted_apply, false) as converted_apply, coalesce(k.converted_sign, false) as converted_sign
from leads l left join (select lead_id, bool_or(match_apply) converted_apply, bool_or(match_sign) converted_sign
                        from lead_contract_link group by 1) k using (lead_id)""")
con.execute(f"copy leads to '{OUT}leads.csv' (format csv, header)")

# ---------------------------------------------------------------- EMP_2_SALESROOM
con.execute(f"create table e_raw as select * from read_csv('{RAW}emp_2_salesroom.csv')")
b = n("select count(*) from e_raw")
con.execute("""
create table emp_2_salesroom as
select distinct role, skp_salesroom, skp_employee, dtime_valid_from,
       case when year(dtime_valid_to) = 3000 then NULL else dtime_valid_to end as dtime_valid_to,
       code_status, code_status = 'a' as is_current
from e_raw""")
note("emp_2_salesroom", "drop exact dup + valid_to 3000 -> NULL", b, n("select count(*) from emp_2_salesroom"))
con.execute(f"copy emp_2_salesroom to '{OUT}emp_2_salesroom.csv' (format csv, header)")

# ---------------------------------------------------------------- LOG
pd.DataFrame(log).to_csv(OUT + "cleaning_log.csv", index=False, encoding="utf-8-sig")
print(f"\nDone -> {OUT}")
