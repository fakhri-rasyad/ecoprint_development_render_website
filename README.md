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

4. Definisikan variabel DATABASE_URL yang akan diisi url dari postgresql pada file .env.
   ```shell
   DATABASE_URL=postgresql://<username>:<password>@localhost:<port>/<nama_tabel_database>
   ```
5. Jalankan aplikasi menggunakan command

   ```shell
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

# WebSocket Routes

## ESP Client

Membuat koneksi websocket dengan ESP

### URL

`ws://api.hiliriset-ecoprint.site/ws/esps/{esp_mac_address}`

### Request Data

Data yang perlu dikirimkan ke API merupakan string alamat MAC esp yang telah didaftarkan pada API
| Parameter | Tipe Data | Deskripsi | Requirement Type |
| ------------- |-------------| -----| ----- |
| esp_mac_address | string | alamat_mac_address pengguna | required |

### Contoh Request koneksi

`ws://api.hiliriset-ecoprint.site/ws/esps/30:AE:A4:07:0D:64`

### Response apabila ESP belum terdaftar

```
{
   "error": "ESP not registered"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| error     | string    | Pesan error simpel |

### Response apabila ESP mengirim data tapi tidak terdapat sesi yang berjalan

```
{
   "warning": "No active boiling session. Data ignored."
}
```

| Parameter | Tipe Data | Deskripsi         |
| --------- | --------- | ----------------- |
| warning   | string    | Peringatan sistem |

### Sinyal Start dari Sistem

Sinyal yang dikirimkan kepada ESP apabila pengguna memulai proses pengukusan

{
"event": "session_start",  
 "fabric_type": fabric_type.name,
"boiling_temp": fabric_type.boiling_temp,
"boiling_time": fabric_type.boiling_time,
"session_id": fabric_session.id
}

| Parameter    | Tipe Data   | Deskripsi                           |
| ------------ | ----------- | ----------------------------------- |
| event        | string      | Sinyal mulai                        |
| fabric_type  | string      | Nama tipe kain                      |
| boiling_temp | float       | Suhu pengukusan kain                |
| boiling_time | int (Menit) | Waktu pengukusan kain dalam menit   |
| session_id   | int         | Id dari sesi pengukusan pada sistem |

## Mobile Client

Membuat koneksi websocket dengan aplikasi mobile

### URL

`ws://api.hiliriset-ecoprint.site/ws/mobile/{session_id}`

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
   "error": "Session not found"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| error     | string    | Pesan error simpel |

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

{
"event": "sensor_update",  
"data" :
{
"humidity": 0.0 (float),
"water_temperature": 0.0 (float),
"air_temperature": 0.0 (float),
water_sufficient" : boolean,
is_started: boolean,
is_done: boolean,
}
}

| Parameter         | Tipe Data | Deskripsi                  |
| ----------------- | --------- | -------------------------- |
| event             | string    | Sinyal update              |
| humidity          | float     | Nilai kelembapan           |
| water_temperature | float     | Suhu air pengukusan kain   |
| air_temeprature   | float     | Suhu udara pengukusan kain |
| is_started        | boolean   | Sinyal sesi mulai          |
| is_done           | boolean   | Sinyal sesi selesai        |
