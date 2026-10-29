# Kirim-chiqimlarni nazorat qiluvchi dastur

Najot Ta'lim Backend Python Django (Standart) kursi 8-oy yakuniy imtihoni uchun o'quv loyihasi. API foydalanuvchiga shaxsiy kirim, chiqim, kategoriyalar va moliyaviy hisobotlarni yuritish imkonini beradi.

## 1. Texnologiyalar

- Python 3.12
- Django 5.2.18
- Django REST Framework 3.17.2
- JWT: `djangorestframework-simplejwt` 5.5.1
- Swagger/ReDoc: `drf-spectacular` 0.30.0
- SQLite
- Docker va Docker Compose
- Postman Collection 2.1

## 2. Loyihaning papkalari

```text
kirim_chiqim_exam/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── finance/
│   ├── migrations/
│   │   ├── __init__.py
│   │   └── 0001_initial.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── data/
│   └── .gitkeep
├── postman/
│   └── Kirim_Chiqim_API.postman_collection.json
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── README.md
├── POSTMAN_QOLLANMA.md
└── HIMOYA_MATNI.md
```

SQLite fayli ishga tushgandan keyin `data/db.sqlite3` ichida yaratiladi. Bu fayl GitHub'ga yuborilmaydi.

## 3. Muhim eslatmalar

- `SECRET_KEY` va `DEBUG=True` o'quv muhiti uchun yozilgan. Haqiqiy ishlab chiqarish loyihasida maxfiy kalitni kod ichida ochiq saqlash, `DEBUG=True` qoldirish yoki barcha hostlarga ruxsat berish tavsiya etilmaydi.
- `settings.py` ichidagi USD va EUR kurslari faqat **sinov uchun**. Bu haqiqiy yoki yangilanib turadigan bozor kursi emas.
- Hisobotlarning asosiy valyutasi UZS. Statistikada `amount_uzs` yig'indisi ishlatiladi.
- Oddiy foydalanuvchi JWT token orqali faqat o'z ma'lumotlarini ko'radi. `is_staff`/admin huquqini ro'yxatdan o'tish endpointidan yuborib bo'lmaydi.
- `transaction_date` berilmasa, Toshkent mahalliy sanasi ishlatiladi.

## 4. Windows'da lokal ishga tushirish

Terminal yoki PowerShell'ni `manage.py` va `docker-compose.yml` turgan loyiha ildiz papkasida oching. `no configuration file provided: not found` xatosi ko'pincha terminal noto'g'ri papkada turganida chiqadi.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Agar PowerShell virtual muhitni faollashtirishga ruxsat bermasa, Windows CMD oynasida quyidagidan foydalaning:

```bat
.venv\Scripts\activate.bat
```

Server muvaffaqiyatli ishga tushgach, API `http://127.0.0.1:8000/` portida ishlaydi.

### Superuser yaratish

`python manage.py createsuperuser` buyrug'idan keyin username, email (so'ralsa) va parol kiriting. Parol terilayotganda ekranda ko'rinmasligi normal holat. Admin panel: `http://127.0.0.1:8000/admin/`.

## 5. Docker orqali ishga tushirish

Docker Desktop o'rnatilgan va ishga tushgan bo'lishi kerak. Loyiha ildiz papkasida:

```powershell
docker compose up --build
```

Bu buyruq image quradi, `data` papkasini konteynerga ulaydi, migratsiyalarni qo'llaydi va serverni 8000-portda ishga tushiradi. Keyingi safar oddiy `docker compose up` yetarli bo'ladi.

Boshqa terminaldan Docker ichida admin yaratish:

```powershell
docker compose exec web python manage.py createsuperuser
```

To'xtatish: `Ctrl+C`, keyin kerak bo'lsa `docker compose down`. SQLite bazasi `./data/db.sqlite3` ichida qoladi. `data/db.sqlite3` faylini o'chirsangiz, ma'lumotlar bazasi ham o'chadi.

## 6. Hujjatlar

- Swagger UI: <http://127.0.0.1:8000/api/docs/>
- ReDoc: <http://127.0.0.1:8000/api/redoc/>
- OpenAPI schema: <http://127.0.0.1:8000/api/schema/>
- Django admin: <http://127.0.0.1:8000/admin/>

Swagger'da himoyalangan API'larni tekshirish uchun avval `/api/auth/token/` orqali `access` token oling. Swagger sahifasidagi **Authorize** tugmasini bosing va `Bearer <access_token>` qiymatini kiriting. So'ngra **Authorize** va **Close** ni bosing.

## 7. API endpointlari

### Autentifikatsiya

| Metod | Endpoint | Vazifasi |
|---|---|---|
| POST | `/api/auth/register/` | Oddiy foydalanuvchi yaratish |
| POST | `/api/auth/token/` | `access` va `refresh` JWT olish |
| POST | `/api/auth/token/refresh/` | Yangi `access` token olish |

Token olish misoli:

```json
{
  "username": "exam_user_01",
  "password": "UzFinance#2026Secure"
}
```

Ro'yxatdan o'tish javobida token berilmaydi; alohida token endpointiga kirish kerak. Login standart Django `username` va `password` orqali ishlaydi.

### Kategoriyalar

`GET`, `POST` `/api/categories/`; `GET`, `PUT`, `PATCH`, `DELETE` `/api/categories/{id}/`.

Kiritish namunasi:

```json
{
  "name": "Maosh",
  "kind": "INCOME",
  "description": "Oylik ish haqi"
}
```

### Tranzaksiyalar

`GET`, `POST` `/api/transactions/`; `GET`, `PUT`, `PATCH`, `DELETE` `/api/transactions/{id}/`.

Kiritish namunasi:

```json
{
  "category": 1,
  "kind": "INCOME",
  "amount": "10.00",
  "currency": "USD",
  "description": "Dollar ko'rinishidagi kirim",
  "transaction_date": "2026-10-28"
}
```

`exchange_rate` va `amount_uzs` ni so'rovda yubormang. Ularni server o'zi hisoblaydi. USD kursi 12600 bo'lsa, 10 USD `126000.00 UZS` bo'ladi.

Filtrlar misoli:

- `/api/transactions/?kind=INCOME`
- `/api/transactions/?currency=USD`
- `/api/transactions/?date_from=2026-10-01&date_to=2026-10-31`
- Filtrlarni birlashtirish mumkin: `/api/transactions/?kind=EXPENSE&currency=UZS&date_from=2026-10-01`

### Hisobotlar

- `GET /api/reports/daily/`
- `GET /api/reports/weekly/`
- `GET /api/reports/monthly/`

Odatiy holatda bugungi sana asos qilib olinadi. Istalgan sanani tanlash uchun `?date=YYYY-MM-DD` qo'shing. Haftalik hisobot dushanbadan yakshanbagacha, oylik hisobot oyning birinchi kunidan oxirgi kunigacha hisoblanadi. Hisobotlarda jami kirim, jami chiqim, balans, tranzaksiyalar soni va kategoriya kesimidagi yig'indilar beriladi.

## 8. Postman Collection

Fayl: https://documenter.getpostman.com/view/56010445/2sBYHVwezf

1. Postman'da **Import** tugmasini bosing.
2. Collection JSON faylini tanlang.
3. Collection ichidagi so'rovlarni yuqoridan pastga qarab ishga tushiring: Register → Token olish → Token refresh → kategoriyalar → tranzaksiyalar → hisobotlar → tranzaksiyalarni o'chirish → kategoriyalarni o'chirish.
4. Register so'rovi username va email uchun vaqt belgisidan foydalanib, har bir qayta sinovda yangi foydalanuvchi yaratadi.
5. Token so'rovidagi test skripti `access_token` va `refresh_token` collection variable'larini avtomatik saqlaydi. Himoyalangan so'rovlar `Bearer {{access_token}}` ishlatadi.
6. Agar bir so'rovni alohida yuborsangiz, kerakli oldingi bosqichlar bajarilgan va collection variable'lari qiymatga ega ekanini tekshiring.

Batafsil ketma-ketlik `POSTMAN_QOLLANMA.md` faylida va Postman Collection ichida ko'rsatilgan.

## 9. Oddiy foydalanuvchi va admin

- **Oddiy foydalanuvchi:** `/api/auth/register/` orqali yaratiladi; keyin username/password bilan JWT oladi. Faqat o'z kategoriyasi va tranzaksiyalarini boshqaradi.
- **Admin/superuser:** `createsuperuser` orqali yaratiladi. Django admin panelida barcha kategoriyalar va tranzaksiyalarni ko'rishi va boshqarishi mumkin. `is_staff` va `is_superuser` maydonlari ro'yxatdan o'tish serializerida yo'q.

## 10. GitHub'ga joylash

Git o'rnatilgan va terminal loyiha ildizida turgan bo'lsin:

```bash
git init
git add .
git commit -m "Kirim-chiqim API loyihasi"
git branch -M main
git remote add origin https://github.com/USERNAME/kirim_chiqim_exam.git
git push -u origin main
```

`USERNAME` va repo URL'ini o'zingizning GitHub hisobingiz bilan almashtiring. `data/db.sqlite3` `.gitignore` sababli commit qilinmaydi.

## 11. Muammolarni tez tekshirish

- `no configuration file provided: not found`: terminal loyiha ildizida emas yoki `docker-compose.yml` nomi/joyi noto'g'ri. Avval `dir` buyrug'i bilan fayllarni tekshiring va kerakli papkaga `cd` qiling.
- `ModuleNotFoundError`: virtual muhit faolligini tekshirib, `pip install -r requirements.txt` bajaring.
- `401 Unauthorized`: access token muddati tugagan yoki `Authorization: Bearer ...` headeri yo'q/noto'g'ri.
- `403 Forbidden`: foydalanuvchida kerakli ruxsat yo'q.
- `400 Bad Request`: response ichidagi maydon xabarlarini o'qing; masalan, kategoriya turi bilan tranzaksiya turi mos bo'lishi kerak.
- Kategoriya o'chmayapti: unga bog'langan tranzaksiyalar bor. Avval shu tranzaksiyalarni o'chiring yoki boshqa kategoriya yarating.
- Docker ishlamayapti: Docker Desktop ishga tushganini tekshiring.

## 12. Asosiy kod qanday ishlaydi?

- `models.py`: SQLite'dagi Category va Transaction jadvallarini belgilaydi.
- `serializers.py`: so'rov ma'lumotlarini tekshiradi, parolni xavfsiz yaratadi va valyuta konvertatsiyasini hisoblaydi.
- `views.py`: API endpointlarining ishlashini, egaga tegishlilikni, filtrlarni va hisobotlarni bajaradi.
- `urls.py`: URL yo'llarini view'lar bilan bog'laydi.
- `admin.py`: Django admin ro'yxatlarini, qidiruv/filtrlarni va admin'da valyuta qayta hisoblashni sozlaydi.
- `settings.py`: Django, SQLite, vaqt zonasi, JWT, valyuta kurslari va Swagger sozlamalarini saqlaydi.
- `0001_initial.py`: kategoriyalar va tranzaksiyalar jadvallarini yaratadigan migratsiya.

Video uchun sodda himoya matni `HIMOYA_MATNI.md` faylida.
