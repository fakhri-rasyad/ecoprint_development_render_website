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
   "event": "esp_not_registered"
}
```

| Parameter | Tipe Data | Deskripsi          |
| --------- | --------- | ------------------ |
| event     | string    | Pesan error simpel |

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
