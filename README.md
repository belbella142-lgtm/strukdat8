# strukdat8
📝 Note-Taking App — Struktur Data

Implementasi struktur data untuk aplikasi note-taking menggunakan Python murni (tanpa library eksternal).

📋 Deskripsi

Proyek ini adalah tugas perancangan struktur data yang mengimplementasikan tiga fitur utama:

| Fitur | Struktur Data |
|-------|--------------|
| Multiple tags per note | Multi-linked list (many-to-many) |
| Chronological & alphabetical views | Doubly Linked List (terurut) |
| Sync status tracking | Circular Buffer |

🗂️ Struktur File

```
note_app.py     ← seluruh implementasi dalam satu file
README.md       ← dokumentasi ini
```

🏗️ Arsitektur Kelas

```
┌──────────────────────────────────────────────────┐
│                    NoteApp                       │
│                                                  │
│  chrono_list ──► DoublyLinkedList (by date)      │
│  alpha_list  ──► DoublyLinkedList (by title)     │
│  tag_index   ──► { str : TagNode }               │
│  note_index  ──► { str : NoteNode }              │
│  sync_buffer ──► CircularBuffer                  │
└──────────────────────────────────────────────────┘
         │                  │
         ▼                  ▼
     NoteNode           TagNode
   (doubly linked)   (multi-linked)
```

`NoteNode`
Node utama yang merepresentasikan satu catatan. Setiap node memiliki dua pasang pointer (`prev/next`) untuk dua linked list yang berbeda (kronologis dan alfabetis), serta daftar tag yang dimilikinya.

`TagNode`
Node yang merepresentasikan sebuah tag. Menyimpan referensi ke semua note yang memiliki tag tersebut, membentuk relasi **many-to-many** antara note dan tag.

`DoublyLinkedList`
Doubly linked list yang selalu dalam kondisi terurut. Mendukung dua mode pengurutan:
- `chrono` — urut berdasarkan `created_at` (terlama → terbaru)
- `alpha` — urut berdasarkan `title` (A → Z, case-insensitive)

`CircularBuffer`
Buffer berkapasitas tetap (default: 10 slot) untuk mencatat perubahan terbaru. Ketika penuh, entri paling lama otomatis ditimpa. Berfungsi sebagai antrian FIFO untuk memproses sinkronisasi.

`NoteApp`
Kelas utama yang mengintegrasikan semua struktur di atas. Menyediakan antarmuka publik untuk operasi CRUD dan manajemen sinkronisasi.

⚙️ Cara Penggunaan

Prasyarat
- Python 3.10 atau lebih baru (menggunakan type hint `X | Y`)
- Tidak memerlukan library eksternal

Menjalankan Demo

```bash
python note_app.py
```

Contoh Penggunaan dalam Kode

```python
from note_app import NoteApp

# Inisialisasi aplikasi
app = NoteApp(sync_buffer_size=10)

# Tambah note dengan beberapa tag
note = app.add_note(
    title   = "Belajar Python",
    content = "Materi OOP dan linked list",
    tags    = ["kuliah", "penting"]
)

# Tampilkan semua note
app.view_chrono()   # urut berdasarkan waktu dibuat
app.view_alpha()    # urut berdasarkan judul (A-Z)

# Cari note berdasarkan tag
app.find_by_tag("penting")

# Proses antrian sinkronisasi
app.show_sync_buffer()
app.process_sync()

# Hapus note
app.delete_note(note.id)
```
📊 Kompleksitas

| Operasi | Time Complexity | Keterangan |
|---------|----------------|------------|
| `add_note` | O(n) | Insert terurut ke dua linked list |
| `delete_note` | O(1) | Pointer langsung via `note_index` |
| `find_by_tag` | O(1) | Lookup via `tag_index` dictionary |
| `view_chrono / alpha` | O(n) | Traverse linked list |
| `sync_buffer.push` | O(1) | Tulis ke slot buffer |
| `sync_buffer.pop` | O(1) | Baca dari slot buffer |

🔍 Contoh Output

```
=======================================================
   NOTE-TAKING APP — Demo Struktur Data
=======================================================
[+] Note ditambahkan: Note(id=635e196a, title='Belajar Python', ...)

📅  Chronological View:
  1. [11:20:40] Belajar Python | tags=['kuliah', 'penting']
  2. [11:20:40] Agenda Rapat   | tags=['kerja', 'penting']
  ...

🔤  Alphabetical View:
  1. Agenda Rapat    | tags=['kerja', 'penting']
  2. Algoritma Sorting | tags=['kuliah']
  3. Belajar Python  | tags=['kuliah', 'penting']
  ...

🏷️  Notes dengan tag='penting':
  • Belajar Python  (id=635e196a)
  • Agenda Rapat    (id=e56fae34)
  • Deadline Proyek (id=7cb68a6c)

🔄  Memproses sync buffer...
  ✓ Synced: {'note_id': '635e196a', 'action': 'create', ...}
  Total diproses: 5 event(s)
```

📐 Diagram Relasi

```
Note A ──┬── Tag "kuliah"  ◄──── Note C
         └── Tag "penting" ◄──── Note B
                                 Note A

chrono_list:  [Note A] ↔ [Note B] ↔ [Note C]   (urut waktu)
alpha_list:   [Note B] ↔ [Note C] ↔ [Note A]   (urut judul A-Z)

sync_buffer:  [ ev1 | ev2 | ev3 | ev4 | ev5 ]
               ↑ head                    ↑ tail
```
👤 Informasi

> Tugas Struktur Data — Implementasi Multi-Linked List, Doubly Linked List, dan Circular Buffer
