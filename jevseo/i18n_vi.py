"""Vietnamese labels for the web interface: areas, severities and every rule's title and fix.

The audit engine and the reports stay in English; the web app shows these alongside.
"""
from __future__ import annotations

CATEGORIES = {
    "crawl": "Thu thập và lập chỉ mục",
    "onpage": "On-page",
    "content": "Chất lượng nội dung",
    "links": "Liên kết và cấu trúc",
    "structured": "Dữ liệu có cấu trúc và chia sẻ",
    "ai": "Sẵn sàng cho tìm kiếm AI",
    "performance": "Hiệu năng",
    "security": "Bảo mật và tin cậy",
    "visibility": "Hiển thị tìm kiếm và uy tín",
}

SEVERITY = {"critical": "Nghiêm trọng", "high": "Cao", "medium": "Trung bình", "low": "Thấp", "info": "Thông tin"}

# id: (title, fix)
RULES = {
    "robots_missing": ("Không có tệp robots.txt", "Đặt tệp robots.txt ở thư mục gốc, cho phép thu thập và khai báo sitemap."),
    "robots_blocks_site": ("robots.txt chặn công cụ tìm kiếm trên toàn site", "Bỏ lệnh Disallow toàn site dành cho các user agent của công cụ tìm kiếm."),
    "sitemap_missing": ("Không tìm thấy sitemap XML", "Tạo sitemap XML gồm các URL chuẩn, có thể lập chỉ mục, và khai báo nó trong robots.txt."),
    "sitemap_errors": ("Tệp sitemap không truy cập được hoặc không hợp lệ", "Sửa URL sitemap để trả về HTTP 200 với XML hợp lệ."),
    "sitemap_bad_urls": ("Sitemap chứa URL chuyển hướng, lỗi hoặc noindex", "Chỉ liệt kê URL cuối cùng, trả về HTTP 200 và có thể lập chỉ mục."),
    "not_in_sitemap": ("Trang có thể lập chỉ mục nhưng thiếu trong sitemap", "Thêm các trang chuẩn này vào sitemap."),
    "http_errors": ("Trang trả về lỗi HTTP", "Khôi phục các URL này hoặc chuyển hướng tới trang tương đương còn hoạt động, rồi cập nhật liên kết."),
    "broken_internal_links": ("Liên kết nội bộ trỏ tới URL hỏng", "Sửa hoặc bỏ các liên kết trỏ tới URL lỗi 4xx, 5xx hoặc không truy cập được."),
    "redirect_chains": ("Chuỗi chuyển hướng (nhiều hơn một bước)", "Cho mỗi chuyển hướng trỏ thẳng tới URL cuối cùng."),
    "links_to_redirects": ("Liên kết nội bộ đi qua chuyển hướng", "Liên kết trực tiếp tới URL cuối cùng."),
    "noindex": ("Trang bị loại khỏi tìm kiếm bằng noindex", "Xác nhận từng noindex là có chủ ý; bỏ noindex ở những trang cần xếp hạng."),
    "canonical_missing": ("Trang không có thẻ canonical", "Thêm rel=canonical tự tham chiếu cho mỗi trang có thể lập chỉ mục."),
    "canonical_elsewhere": ("Canonical trỏ tới URL khác", "Kiểm tra các trang này có thật là bản trùng của trang đích không; nếu không, để canonical tự trỏ về chính nó."),
    "canonical_broken": ("Đích canonical chuyển hướng hoặc bị lỗi", "Trỏ canonical tới URL còn hoạt động và có thể lập chỉ mục."),
    "soft_404": ("Trang không tồn tại vẫn trả về HTTP 200 (soft 404)", "Trả về mã 404 hoặc 410 thật cho URL không tồn tại."),
    "host_temporary_redirect": ("Chuyển hướng tên miền hoặc HTTPS là tạm thời (302 hoặc 307)", "Dùng chuyển hướng vĩnh viễn (301 hoặc 308) cho www, không www và HTTP sang HTTPS."),
    "host_variant": ("Cả www và không www đều hiển thị site", "Chuyển hướng vĩnh viễn tên miền phụ về tên miền chính."),
    "no_https": ("Site không chạy HTTPS, hoặc HTTP không chuyển sang HTTPS", "Phục vụ mọi trang qua HTTPS và chuyển hướng vĩnh viễn HTTP sang HTTPS."),
    "deep_pages": ("Trang cách trang chủ hơn ba lần nhấp", "Liên kết các trang sâu quan trọng từ trang chuyên mục hoặc menu gần trang chủ hơn."),
    "orphan_pages": ("Trang trong sitemap không có liên kết nội bộ (trang mồ côi)", "Liên kết tới các trang này từ những trang liên quan."),
    "js_dependent": ("Nội dung chỉ hiện sau khi JavaScript chạy", "Render phía server hoặc pre-render nội dung và liên kết chính."),
    "title_missing": ("Trang không có thẻ title", "Viết title riêng, mô tả rõ cho từng trang."),
    "title_duplicate": ("Title bị trùng giữa các trang", "Đặt cho mỗi trang một title phân biệt với các trang khác."),
    "title_length": ("Title quá ngắn hoặc quá dài", "Viết title ngắn gọn, mô tả rõ. Google cắt theo độ rộng pixel; 15 đến 65 ký tự là quy ước hiển thị."),
    "multiple_titles": ("Có nhiều hơn một thẻ title", "Chỉ giữ một thẻ title trong phần head."),
    "meta_missing": ("Trang không có meta description", "Viết đoạn tóm tắt riêng cho trang. Google vẫn có thể tự tạo đoạn trích."),
    "meta_duplicate": ("Meta description bị trùng", "Viết description khác nhau cho từng trang."),
    "h1_missing": ("Trang không có thẻ H1", "Cho mỗi trang một tiêu đề chính hiển thị, nêu rõ chủ đề."),
    "h1_multiple": ("Trang có nhiều thẻ H1", "Dùng một tiêu đề chính, các phần dùng H2 trở xuống."),
    "heading_skips": ("Bỏ qua cấp tiêu đề", "Sắp xếp tiêu đề theo thứ tự (H2 dưới H1, H3 dưới H2)."),
    "lang_missing": ("Thiếu thuộc tính lang của HTML", "Khai báo ngôn ngữ trang trên thẻ html."),
    "viewport_missing": ("Thiếu thẻ meta viewport cho di động", "Thêm thẻ meta viewport responsive."),
    "thin_content": ("Trang có rất ít nội dung chính", "Bổ sung nội dung hữu ích cho trang cần xếp hạng, hoặc gộp trang. Số từ là dấu hiệu cảnh báo, không phải yếu tố xếp hạng."),
    "duplicate_content": ("Trang có nội dung chính giống hệt nhau", "Gộp các trang trùng hoặc đặt canonical về một URL."),
    "images_alt": ("Ảnh thiếu thuộc tính alt", "Thêm alt mô tả cho ảnh mang thông tin; dùng alt rỗng cho ảnh trang trí."),
    "images_dimensions": ("Ảnh thiếu width và height", "Đặt width và height để bố cục không bị xê dịch khi ảnh tải."),
    "no_structured_data": ("Trang chủ không có dữ liệu có cấu trúc", "Thêm JSON-LD mô tả tổ chức và website (ví dụ Organization và WebSite)."),
    "jsonld_errors": ("Dữ liệu có cấu trúc không đọc được", "Sửa cú pháp JSON-LD để công cụ tìm kiếm đọc được."),
    "schema_required": ("Dữ liệu có cấu trúc thiếu thuộc tính Google yêu cầu cho kết quả nhiều định dạng", "Thêm các thuộc tính bắt buộc còn thiếu, hoặc bỏ markup không thể điền trung thực."),
    "faq_rich_result_limited": ("FAQPage: kết quả nhiều định dạng chỉ dành cho site chính phủ và y tế", "Có thể giữ markup, nhưng đừng kỳ vọng hiển thị FAQ trừ khi là cơ quan chính phủ hoặc y tế uy tín."),
    "og_missing": ("Thiếu Open Graph title hoặc image", "Thêm og:title, og:description và og:image để xem trước khi chia sẻ link."),
    "hreflang_issues": ("Khai báo hreflang chưa đầy đủ", "Mỗi phiên bản ngôn ngữ cần tự tham chiếu và có liên kết ngược; thêm x-default khi cần."),
    "ai_bots_blocked": ("Bot AI bị chặn trong robots.txt", "Hãy quyết định có chủ ý. Chặn Google-Extended không ảnh hưởng Google Search; chặn bot AI tìm kiếm có thể làm site biến mất khỏi các công cụ trả lời đó."),
    "llms_txt_missing": ("Không có tệp llms.txt", "Không bắt buộc. llms.txt là đề xuất của cộng đồng, không phải yêu cầu của công cụ tìm kiếm."),
    "hsts_missing": ("Không có header Strict-Transport-Security", "Gửi header HSTS khi HTTPS đã ổn định trên toàn site."),
    "security_headers": ("Thiếu các header bảo mật phổ biến", "Thêm X-Content-Type-Options, Referrer-Policy và chính sách frame."),
    "mixed_content": ("Trang HTTPS tải tài nguyên HTTP", "Tải mọi tài nguyên qua HTTPS."),
    "favicon_missing": ("Chưa khai báo favicon", "Khai báo favicon; Google hiển thị nó cạnh kết quả tìm kiếm."),
    "slow_ttfb": ("Máy chủ phản hồi chậm (TTFB trên 0,8 giây)", "Dùng cache, CDN và giảm xử lý phía server trước byte đầu tiên."),
    "heavy_html": ("Tài liệu HTML quá lớn (trên 500 KB)", "Cắt bớt dữ liệu inline và markup đi kèm mọi trang."),
    "generic_anchors": ("Liên kết nội bộ dùng anchor text chung chung", "Dùng anchor text mô tả trang đích."),
    "broken_external_links": ("Liên kết ra ngoài bị lỗi", "Sửa hoặc bỏ liên kết ra ngoài không còn hoạt động."),
    "cwv_field": ("Core Web Vitals chưa đạt mức tốt với người dùng di động thật", "Xử lý các đề xuất của PageSpeed cho các chỉ số chưa đạt, bắt đầu từ mục tiết kiệm nhiều nhất."),
    "lab_performance": ("Điểm hiệu năng Lighthouse trên di động thấp", "Giảm tài nguyên chặn render, dung lượng ảnh và JavaScript; xem đề xuất của PageSpeed."),
    "jev_value_prop": ("Trang chủ chưa nêu rõ sản phẩm, dịch vụ", "Nêu rõ bạn cung cấp gì, cho ai và vì sao nên chọn bạn ngay màn hình đầu tiên."),
    "jev_entity_clarity": ("Trang chủ chưa nói rõ ai, làm gì, ở đâu", "Nêu tên tổ chức, lĩnh vực và thị trường hoặc địa điểm bằng lời rõ ràng ở đầu trang."),
    "jev_local_schema": ("Doanh nghiệp địa phương thiếu LocalBusiness schema", "Thêm JSON-LD LocalBusiness với tên, địa chỉ, điện thoại và giờ mở cửa khớp với trang."),
    "jev_helpfulness": ("Trang quan trọng chưa đáp ứng người đọc", "Bổ sung câu trả lời, chi tiết, ví dụ và bước tiếp theo mà người đọc cần."),
    "jev_specificity": ("Nội dung chung chung, đối thủ nào cũng viết được", "Thêm chi tiết thực tế: số liệu, quy trình, ví dụ, địa điểm, tên người và kết quả của chính bạn."),
    "jev_trust": ("Trang chính ít bằng chứng chuyên môn hoặc độ tin cậy", "Thêm tên người, chứng chỉ, đánh giá, nguồn, kết quả và thông tin liên hệ."),
    "jev_next_step": ("Trang thương mại không có bước tiếp theo rõ ràng", "Mỗi trang thương mại cần một lời kêu gọi hành động rõ và phù hợp."),
    "jev_title_fit": ("Title chưa mô tả đúng trang", "Viết lại title nêu rõ trang cung cấp gì bằng từ ngữ người tìm kiếm dùng."),
    "jev_meta_fit": ("Meta description yếu", "Viết lại description thành tóm tắt cụ thể những gì trang mang lại."),
    "jev_h1_fit": ("H1 chưa nêu chủ đề", "Để H1 gọi tên chủ đề của trang thay vì khẩu hiệu."),
    "jev_answer_first": ("Trang giấu ý chính", "Mở đầu bằng một hai câu trả lời hoặc lời đề nghị trước phần dẫn dắt."),
    "jev_citable": ("Ít dữ kiện rõ ràng, dễ trích dẫn", "Thêm định nghĩa, số liệu và khẳng định rõ ràng, đọc riêng vẫn hiểu."),
    "jev_rewrite": ("Trang Jev đề xuất viết lại hoặc gộp", "Xem lại từng trang theo đề xuất. Đây là đánh giá biên tập của Jev, không phải quy tắc của công cụ tìm kiếm."),
    "jev_cannibalization": ("Các trang cạnh tranh cùng từ khóa", "Mỗi nhu cầu tìm kiếm chỉ một trang: gộp, tạo khác biệt, hoặc canonical trang yếu hơn."),
    "dfs_striking": ("Từ khóa liên quan gần lên trang một", "Củng cố trang đang xếp hạng: trả lời đầy đủ hơn, thêm liên kết nội bộ và chỉnh title."),
    "dfs_existing_page": ("Từ khóa mà trang hiện có có thể giành được", "Mở rộng trang được nêu để đáp ứng nhu cầu của từng từ khóa, rồi liên kết tới nó."),
    "dfs_new_page": ("Từ khóa liên quan chưa có trang để xếp hạng", "Mỗi nhu cầu tìm kiếm một trang; bắt đầu từ từ khóa lượng tìm cao, độ khó thấp."),
    "dfs_backlink_gap": ("Ít tên miền giới thiệu hơn nhiều so với đối thủ", "Xây dựng liên kết từ các site khán giả của bạn đọc: dữ liệu gốc, công cụ, bài chuyên gia, đối tác."),
    "dfs_broken_backlinks": ("Backlink trỏ tới trang hỏng", "Chuyển hướng từng trang hỏng tới trang còn hoạt động gần nhất."),
    "dfs_aio_not_cited": ("AI Overviews không trích dẫn site", "Xem ai đang được trích dẫn và đảm bảo trang trả lời trực tiếp truy vấn."),
}


def localize_action(a: dict) -> dict:
    """Add Vietnamese title and fix to an action row, falling back to the English text."""
    title, fix = RULES.get(a.get("id"), (None, None))
    return a | {
        "title_vi": title or a.get("title"),
        "fix_vi": fix or a.get("fix"),
        "category_vi": CATEGORIES.get(a.get("category"), a.get("category")),
        "severity_vi": SEVERITY.get(a.get("severity"), a.get("severity")),
    }
