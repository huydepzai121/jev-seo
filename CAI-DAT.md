# Hướng dẫn cài đặt Jev SEO Check

Jev SEO Check là website kiểm tra SEO. Bạn nhập URL, công cụ chấm điểm on-page theo % gần như ngay lập tức, rồi audit toàn site với 52 quy tắc theo Google Search Central. Giao diện mặc định là tiếng Việt, có nút chuyển sang tiếng Anh.

Có ba cách cài. Nếu chưa rõ nên chọn cách nào, hãy dùng **Docker Compose** (cách 1).

| Cách | Phù hợp khi | Cần có |
| --- | --- | --- |
| [1. Docker Compose](#cách-1-docker-compose-khuyên-dùng) | Chạy trên máy cá nhân hoặc VPS, cài một lệnh là xong | Docker Desktop hoặc Docker Engine có Compose v2.24 trở lên |
| [2. Docker (không dùng Compose)](#cách-2-docker-không-dùng-compose) | Chỉ có lệnh `docker` | Docker |
| [3. Python trực tiếp](#cách-3-python-trực-tiếp) | Muốn sửa code hoặc không dùng Docker | Python 3.10 trở lên và thư viện Pango |

Muốn có link công khai để người khác cùng dùng, xem phần [Đưa lên Internet](#đưa-lên-internet).

---

## Chuẩn bị: tải mã nguồn

```sh
git clone https://github.com/huydepzai121/jev-seo.git
cd jev-seo
```

Chưa có Git thì vào trang GitHub của repo, chọn **Code → Download ZIP**, rồi giải nén.

## Khóa API (không bắt buộc)

Không cần khóa nào website vẫn chạy. Có khóa thì kết quả đầy đủ hơn:

| Biến | Tác dụng | Không có thì sao |
| --- | --- | --- |
| `TYPESAFE_API_KEY` | Jev chấm chất lượng nội dung, độ tin cậy, khả năng được AI trích dẫn | Audit vẫn chạy nhưng ghi "Audit một phần", mục chất lượng nội dung hiện "chưa chấm" |
| `PAGESPEED_API_KEY` | Đo Core Web Vitals ổn định hơn (khóa miễn phí trên Google Cloud) | PageSpeed vẫn chạy nhưng dễ bị giới hạn số lượt |
| `DATAFORSEO_USERNAME`, `DATAFORSEO_PASSWORD` | Từ khóa, thứ hạng, backlink (chế độ `--full`, tính phí theo lượt gọi) | Chỉ dùng được ở dòng lệnh, giao diện web không dùng |

Tạo file `.env` từ mẫu rồi điền khóa:

```sh
cp .env.example .env        # Windows: copy .env.example .env
```

```ini
TYPESAFE_API_KEY=khoa-cua-ban
PAGESPEED_API_KEY=khoa-cua-ban
```

File `.env` đã có trong `.gitignore`, nên không bị đưa lên GitHub. Tuyệt đối không commit khóa.

---

## Cách 1: Docker Compose (khuyên dùng)

1. Cài [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows, macOS) hoặc Docker Engine (Linux).
2. Trong thư mục `jev-seo`, chạy:

   ```sh
   docker compose up -d --build
   ```

3. Mở trình duyệt vào **http://localhost:8000**.

Lần build đầu mất vài phút. Kết quả audit và file báo cáo được lưu trong volume `jevseo-data`, nên khởi động lại container không bị mất.

Các lệnh hay dùng:

```sh
docker compose logs -f                 # xem nhật ký
docker compose restart                 # khởi động lại (sau khi sửa .env)
docker compose down                    # dừng
git pull && docker compose up -d --build   # cập nhật phiên bản mới
```

Muốn đổi cổng, ví dụ sang 8080: `JEVSEO_PORT=8080 docker compose up -d`, hoặc thêm dòng `JEVSEO_PORT=8080` vào `.env`.

## Cách 2: Docker (không dùng Compose)

```sh
docker build -t jev-seo .
docker run -d --name jev-seo -p 8000:8000 --env-file .env -v jevseo-data:/data --restart unless-stopped jev-seo
```

Chưa tạo `.env` thì bỏ phần `--env-file .env`. Mở **http://localhost:8000**.

## Cách 3: Python trực tiếp

### Bước 1: cài Python và thư viện hệ thống

WeasyPrint (dùng để xuất PDF) cần thư viện Pango:

| Hệ điều hành | Lệnh |
| --- | --- |
| Ubuntu, Debian | `sudo apt install python3 python3-venv libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b` |
| macOS | `brew install python pango` |
| Fedora | `sudo dnf install python3 pango` |
| Windows | Cài Python 3.10+ từ [python.org](https://www.python.org/downloads/) và chọn "Add python.exe to PATH". Sau đó cài GTK/Pango theo [hướng dẫn của WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows), hoặc dùng WSL, hoặc dùng Docker cho đơn giản |

### Bước 2: cài gói Python

```sh
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 3: kiểm tra và chạy

```sh
bin/jevseo doctor                 # Windows: python -m jevseo doctor
bin/jevseo serve                  # Windows: python -m jevseo serve
```

`doctor` liệt kê thư viện nào đã đủ và khóa nào đang có, nhưng không bao giờ in giá trị khóa. Sau khi chạy `serve`, mở **http://localhost:8000**.

Các tùy chọn của `serve`:

| Tùy chọn | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Đặt `0.0.0.0` để máy khác trong mạng truy cập được |
| `--port` | `8000` | Cổng web |
| `--data-dir` | `jev-seo-reports/web` | Nơi lưu audit và file báo cáo |

Không bắt buộc: chạy `pip install playwright && playwright install chromium` để audit cả những trang chỉ hiện nội dung sau khi JavaScript chạy.

---

## Sử dụng

1. Nhập URL, ví dụ `vnexpress.net` hoặc `https://ten-mien-cua-ban.vn`, rồi bấm **Phân tích**.
2. **Điểm trang này** hiện gần như ngay, chấm theo 20 tiêu chí on-page.
3. **Điểm toàn site** chạy ở nền, thường mất 1 đến 4 phút, có thanh tiến trình. Xong sẽ có điểm từng hạng mục, danh sách việc cần làm P1 đến P3, và nút tải báo cáo PDF, XLSX, MD.
4. Các tab Tóm tắt, Tiêu đề, Hình ảnh, Liên kết, Mạng xã hội, Schema, Công cụ hiển thị chi tiết giống tiện ích SEO META in 1 CLICK. Tiêu đề, Hình ảnh và Liên kết có nút tải CSV.

Mẹo:
- Mở `http://localhost:8000/?url=ten-mien.vn` để phân tích ngay mà không cần gõ.
- Bỏ chọn "Audit toàn site" nếu chỉ cần kiểm tra một trang.
- Chọn 10 trang để audit nhanh, 60 trang để audit kỹ hơn.

Vẫn dùng được dòng lệnh như trước, xem [README.md](README.md):

```sh
bin/jevseo run https://ten-mien.vn          # audit và xuất báo cáo vào jev-seo-reports/
```

---

## Đưa lên Internet

### Render (miễn phí, không cần máy chủ)

1. Merge code vào nhánh `main` trên GitHub.
2. Mở https://render.com/deploy?repo=https://github.com/huydepzai121/jev-seo, đăng nhập bằng GitHub rồi bấm **Deploy**. Render đọc sẵn `render.yaml` trong repo.
3. Điền `TYPESAFE_API_KEY` và `PAGESPEED_API_KEY` nếu có, không có thì để trống.
4. Render cấp link dạng `https://jev-seo-xxxx.onrender.com`.

Gói miễn phí của Render tự tắt khi không có người dùng, nên lần mở đầu tiên sau đó mất khoảng 30 đến 60 giây. Báo cáo cũ cũng mất khi dịch vụ khởi động lại.

### VPS riêng (Ubuntu) với tên miền và HTTPS

```sh
# trên VPS, sau khi cài Docker
git clone https://github.com/huydepzai121/jev-seo.git && cd jev-seo
cp .env.example .env && nano .env
docker compose up -d --build
```

Đặt Nginx phía trước để có HTTPS (`/etc/nginx/sites-available/seo`):

```nginx
server {
    server_name seo.ten-mien-cua-ban.vn;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }
}
```

```sh
sudo ln -s /etc/nginx/sites-available/seo /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d seo.ten-mien-cua-ban.vn     # chứng chỉ HTTPS miễn phí
```

Nếu dùng Nginx, sửa `ports` trong `docker-compose.yml` thành `"127.0.0.1:8000:8000"` để cổng 8000 không mở trực tiếp ra Internet.

Website không có đăng nhập. Nếu để công khai, nên giới hạn truy cập (ví dụ `auth_basic` của Nginx), vì mỗi audit tốn tài nguyên máy chủ và, khi có khóa, tốn cả phí Jev (tối đa 0,25 USD mỗi audit).

---

## Xử lý lỗi thường gặp

| Hiện tượng | Nguyên nhân và cách xử lý |
| --- | --- |
| `cannot load library 'libgobject-2.0-0'` hoặc `doctor` báo `missing system library` | Thiếu Pango. Cài theo bảng ở cách 3, bước 1, hoặc dùng Docker |
| `address already in use` / cổng 8000 bận | Chạy trên cổng khác: `bin/jevseo serve --port 8080` hoặc `JEVSEO_PORT=8080 docker compose up -d` |
| "Không truy cập được trang này" | Website chặn bot, sai tên miền, hoặc máy chủ không ra được Internet. Mở thử URL đó trong trình duyệt để kiểm tra |
| "Từ chối thu thập (địa chỉ nội bộ …)" | Công cụ cố ý chặn `localhost`, `192.168.x.x`, `10.x.x.x`… để tránh bị lợi dụng tấn công mạng nội bộ. Chỉ audit được website công khai |
| Điểm toàn site ghi "Audit một phần" | Thiếu `TYPESAFE_API_KEY` hoặc PageSpeed không trả kết quả. Thêm khóa vào `.env` rồi khởi động lại |
| PageSpeed báo lỗi 429 | Bị giới hạn số lượt. Thêm `PAGESPEED_API_KEY`, hoặc bỏ chọn "Đo Core Web Vitals" |
| Audit đứng ở "Đang chờ trong hàng đợi" | Mỗi lúc chỉ chạy một audit, các audit khác xếp hàng (tối đa 20). Chờ audit trước chạy xong |
| Sửa `.env` nhưng không có tác dụng | Khởi động lại: `docker compose restart` hoặc dừng rồi chạy lại `serve` |

## Gỡ cài đặt

```sh
docker compose down -v        # dừng và xóa cả dữ liệu audit
docker rmi jev-seo            # xóa image
```

Nếu cài bằng Python, chỉ cần xóa thư mục `jev-seo`.
