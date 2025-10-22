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
