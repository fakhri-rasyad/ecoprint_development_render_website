# FASTAPI backend for Local Network

Projek ini merupakan backend yang dikembangkan untuk digunakan sebagai server utama dari hiliriset ecoprint

## Langkah Penggunaan

1. Git clone repository ini
2. Buat virtual environtmen baru pada folder lokal dan aktifkan
   ```shell
   python -m venv venv
   (*Windows) venv/Scripts/Activate
   (*Linux dan MAC) source venv/bin/activate
   ```
3. Install pustaka yang diperlukan menggunakan perintah.

   ```shell
   pip install -r requirements.txt
   ```

4. Definisikan variabel FASTAPI_DATABASE_URL dan ALEMBIC_DATABASE_URL yang akan diisi url dari postgresql pada file .env.
   ```shell
   FASTAPI_DATABASE_URL=postgresql+psycopg2://<fastapi_user>:<fastapi_pass>@localhost:5432/ecoprint
   ALEMBIC_DATABASE_URL=postgresql+psycopg2://<alembic_user>:<alembic_pass>:alembicpass@localhost:5432/ecoprint
   ```
5. Jalankan aplikasi menggunakan command

   ```shell
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

# MQTT Routes (Hanya untuk esp)

ESP menggunakan MQTT untuk komunikasi data telemetry dan menerima perintah.

## Konfigurasi

| Parameter | nilai                       |
| --------- | --------------------------- |
| base_url  | www.hiliriset-ecoprint.site |
| message   | 1833                        |
| client_id | esp_client                  |

## Topik

| topik                       | arah          | peran esp  |
| --------------------------- | ------------- | ---------- |
| "esp/{mac_address}/command  | server -> esp | subscriber |
| esp/{mac_address}/telemetry | esp -> server | publisher  |

ESP menjadi publisher pada topic "esp/{mac_address}/telemetry"
ESP menjadi subscriber pada topic ""esp/{esp_mac}/command"
Data yang perlu dikirimkan merupakan string alamat MAC esp yang telah didaftarkan pada API

### Response apabila sesi tidak ada

```
{
   "event": "no_active_session",
   "message": "Data ignored"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| event     | string    | Pesan error simpel |
| message   | string    | Pesan singkat      |

### Response apabila data dari esps memiliki nilai yang salah

```
{
   "event": "malformed_json"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| event     | string    | Pesan error simpel |

### Response apabila data dari esps memiliki nilai yang kurang

```
{
   "event": "missing_fields",
   "fields" : ["field1","field2",..,"fieldn"]
}
```

| Parameter | Tipe Data | Deskripsi                |
| --------- | --------- | ------------------------ |
| event     | string    | Pesan error simpel       |
| feild     | string    | daftar field yang kurang |

### Response apabila data dari esps mengalami error mengolah data dari esp

```
{
   "event": "bad_payload"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| event     | string    | Pesan error simpel |

### Sinyal Start dari Sistem

Sinyal yang dikirimkan kepada ESP apabila pengguna memulai proses pengukusan

```
{
   "event": "session_start",
   "fabric_type": fabric_type.name,
   "boiling_temp": fabric_type.boiling_temp,
}
```

| Parameter    | Tipe Data | Deskripsi            |
| ------------ | --------- | -------------------- |
| event        | string    | Sinyal mulai         |
| fabric_type  | string    | Nama tipe kain       |
| boiling_temp | float     | Suhu pengukusan kain |

Sinyal yang dikirimkan kepada ESP apabila untuk menghentikan proses pengukusan

```
{
   "event": "session_stop",
}
```

| Parameter | Tipe Data | Deskripsi      |
| --------- | --------- | -------------- |
| event     | string    | Sinyal selesai |

### Sinyal yang diharapkan dari ESP

Sinyal yang dikirimkan dari ESP ke Server

```
{
   "event" : "preparation" atau "steaming"
   "humidity": 0.0 (float),
   "water_temperature": 0.0 (float),
   "air_temperature": 0.0 (float),
   "water_sufficient" : boolean,
}
```

| Parameter         | Tipe Data | Deskripsi                                                                                         |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------- |
| event             | string    | Sinyal untuk menentukan apakah proses pengukusan masih dalam tahap persiapan atau sedang mengukus |
| humidity          | float     | Nilai kelembapan                                                                                  |
| water_temperature | float     | Suhu air pengukusan kain                                                                          |
| air_temeprature   | float     | Suhu udara pengukusan kain                                                                        |
| water_sufficient  | boolean   | Keadaan apakah air dalam kompor cukup atau tidak                                                  |

## Mobile Client

Membuat koneksi websocket dengan aplikasi mobile

### URL

`ws://www.hiliriset-ecoprint.site:8000/ws/mobile/{session_id}`

### Request Data

Data yang perlu dikirimkan ke API merupakan id sesi yang ingin dimonitor
| Parameter | Tipe Data | Deskripsi | Requirement Type |
| ------------- | --------- | ---------------------------- | ---------------- |
| session_id | int | id sesi yang ingin dimonitor | required |

### Contoh Request koneksi

`ws://api.hiliriset-ecoprint.site/ws/mobile/1`

### Response apabila sesi tidak ada

```
{
   "event": "Session not found"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| event     | string    | Pesan error simpel |

### Response apabila ESP tidak terdaftar

```
{
   "error": "ESP not found"
}
```

| Parameter | Tipe Data | Deskripsi         |
| --------- | --------- | ----------------- |
| warning   | string    | Peringatan sistem |

### Sinyal Start dari Sistem

Sinyal yang dikirimkan kepada mobile saat sistem menerima input dari ESP

```
{
   "event" : "preparation" atau "steaming"
   "humidity": 0.0 (float),
   "water_temperature": 0.0 (float),
   "air_temperature": 0.0 (float),
   "water_sufficient" : boolean,
}
```

| Parameter         | Tipe Data | Deskripsi                                                                                         |
| ----------------- | --------- | ------------------------------------------------------------------------------------------------- |
| event             | string    | Sinyal untuk menentukan apakah proses pengukusan masih dalam tahap persiapan atau sedang mengukus |
| humidity          | float     | Nilai kelembapan                                                                                  |
| water_temperature | float     | Suhu air pengukusan kain                                                                          |
| air_temeprature   | float     | Suhu udara pengukusan kain                                                                        |
| water_sufficient  | boolean   | Keadaan apakah air dalam kompor cukup atau tidak                                                  |

Sinyal yang dikirimkan kepada mobile saat sistem selesai menerima input dari ESP

```
{
   "event" : "Pengukusan selesai"
}
```

| Parameter | Tipe Data | Deskripsi   |
| --------- | --------- | ----------- |
| event     | string    | Sinyal stop |
