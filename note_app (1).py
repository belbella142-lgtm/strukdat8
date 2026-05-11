"""
Struktur Data Aplikasi Note-Taking
====================================
Fitur:
  1. Multiple tags per note (multi-linked by tag)
  2. Chronological & alphabetical views (doubly linked sorted)
  3. Sync status tracking (circular buffer for recent changes)
"""

import uuid
from datetime import datetime


# ─────────────────────────────────────────────
#  1. NODE NOTE
# ─────────────────────────────────────────────
class NoteNode:
    def __init__(self, title: str, content: str):
        self.id         = str(uuid.uuid4())[:8]
        self.title      = title
        self.content    = content
        self.created_at = datetime.now()
        self.sync_status = "unsynced"   # "unsynced" | "pending" | "synced"

        # Doubly linked – chronological
        self.prev_chrono = None
        self.next_chrono = None

        # Doubly linked – alphabetical
        self.prev_alpha  = None
        self.next_alpha  = None

        # Multi-linked tags
        self.tags: list["TagNode"] = []

    def __repr__(self):
        tag_names = [t.name for t in self.tags]
        return (f"Note(id={self.id}, title='{self.title}', "
                f"tags={tag_names}, sync='{self.sync_status}', "
                f"created={self.created_at.strftime('%Y-%m-%d %H:%M:%S')})")


# ─────────────────────────────────────────────
#  2. NODE TAG  (multi-linked)
# ─────────────────────────────────────────────
class TagNode:
    def __init__(self, name: str):
        self.name  = name
        self.notes: list[NoteNode] = []

    def __repr__(self):
        return f"Tag('{self.name}', notes={[n.id for n in self.notes]})"


# ─────────────────────────────────────────────
#  3. DOUBLY LINKED LIST  (sorted)
# ─────────────────────────────────────────────
class DoublyLinkedList:
    """
    Menyimpan note dalam urutan terurut.
    sort_by = 'chrono' → urut berdasarkan created_at
    sort_by = 'alpha'  → urut berdasarkan title (case-insensitive)
    """

    def __init__(self, sort_by: str = "chrono"):
        assert sort_by in ("chrono", "alpha"), "sort_by harus 'chrono' atau 'alpha'"
        self.sort_by = sort_by
        self.head: NoteNode | None = None
        self.tail: NoteNode | None = None
        self._size = 0

    # ── helper: ambil pointer sesuai mode ──
    def _prev(self, node: NoteNode) -> NoteNode | None:
        return node.prev_chrono if self.sort_by == "chrono" else node.prev_alpha

    def _next(self, node: NoteNode) -> NoteNode | None:
        return node.next_chrono if self.sort_by == "chrono" else node.next_alpha

    def _set_prev(self, node: NoteNode, val):
        if self.sort_by == "chrono": node.prev_chrono = val
        else:                         node.prev_alpha  = val

    def _set_next(self, node: NoteNode, val):
        if self.sort_by == "chrono": node.next_chrono = val
        else:                         node.next_alpha  = val

    def _key(self, node: NoteNode):
        return node.created_at if self.sort_by == "chrono" else node.title.lower()

    # ── insert terurut ──
    def insert_sorted(self, new_node: NoteNode):
        current = self.head

        # cari posisi yang tepat
        while current is not None:
            if self._key(new_node) <= self._key(current):
                self._insert_before(current, new_node)
                self._size += 1
                return
            current = self._next(current)

        # lebih besar dari semua → append di akhir
        self._append(new_node)
        self._size += 1

    def _insert_before(self, anchor: NoteNode, new_node: NoteNode):
        prev_node = self._prev(anchor)
        self._set_next(new_node, anchor)
        self._set_prev(new_node, prev_node)
        self._set_prev(anchor, new_node)
        if prev_node:
            self._set_next(prev_node, new_node)
        else:
            self.head = new_node

    def _append(self, new_node: NoteNode):
        self._set_prev(new_node, self.tail)
        self._set_next(new_node, None)
        if self.tail:
            self._set_next(self.tail, new_node)
        else:
            self.head = new_node
        self.tail = new_node

    # ── hapus node ──
    def remove(self, node: NoteNode):
        prev_node = self._prev(node)
        next_node = self._next(node)
        if prev_node: self._set_next(prev_node, next_node)
        else:         self.head = next_node
        if next_node: self._set_prev(next_node, prev_node)
        else:         self.tail = prev_node
        self._set_prev(node, None)
        self._set_next(node, None)
        self._size -= 1

    # ── tampilkan semua ──
    def to_list(self) -> list[NoteNode]:
        result, current = [], self.head
        while current:
            result.append(current)
            current = self._next(current)
        return result

    def __len__(self):
        return self._size

    def __repr__(self):
        titles = [n.title for n in self.to_list()]
        return f"DoublyLinkedList(sort_by='{self.sort_by}', notes={titles})"


# ─────────────────────────────────────────────
#  4. CIRCULAR BUFFER  (sync tracking)
# ─────────────────────────────────────────────
class CircularBuffer:
    """
    Menyimpan 'capacity' perubahan terakhir.
    Ketika penuh, entri terlama otomatis ditimpa.
    """

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.buffer   = [None] * capacity
        self.head     = 0   # pointer baca (tertua)
        self.tail     = 0   # pointer tulis (berikutnya)
        self.size     = 0

    def push(self, event: dict):
        """Tambahkan event perubahan baru."""
        self.buffer[self.tail] = event
        self.tail = (self.tail + 1) % self.capacity
        if self.size < self.capacity:
            self.size += 1
        else:
            # buffer penuh: geser head (timpa yang paling lama)
            self.head = (self.head + 1) % self.capacity

    def pop(self) -> dict | None:
        """Ambil event terlama (FIFO) untuk diproses sync."""
        if self.size == 0:
            return None
        event = self.buffer[self.head]
        self.buffer[self.head] = None
        self.head = (self.head + 1) % self.capacity
        self.size -= 1
        return event

    def peek_all(self) -> list[dict]:
        """Lihat semua event tanpa menghapus."""
        result = []
        for i in range(self.size):
            result.append(self.buffer[(self.head + i) % self.capacity])
        return result

    def __len__(self):
        return self.size

    def __repr__(self):
        return f"CircularBuffer(size={self.size}/{self.capacity}, events={self.peek_all()})"


# ─────────────────────────────────────────────
#  5. NOTE APP  (integrasi)
# ─────────────────────────────────────────────
class NoteApp:
    def __init__(self, sync_buffer_size: int = 10):
        self.chrono_list  = DoublyLinkedList(sort_by="chrono")
        self.alpha_list   = DoublyLinkedList(sort_by="alpha")
        self.tag_index: dict[str, TagNode] = {}   # nama_tag → TagNode
        self.note_index: dict[str, NoteNode] = {} # note_id  → NoteNode
        self.sync_buffer  = CircularBuffer(capacity=sync_buffer_size)

    # ── tambah note ──
    def add_note(self, title: str, content: str, tags: list[str]) -> NoteNode:
        note = NoteNode(title, content)

        # masukkan ke kedua linked list
        self.chrono_list.insert_sorted(note)
        self.alpha_list.insert_sorted(note)

        # hubungkan tags (multi-link many-to-many)
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if tag_name not in self.tag_index:
                self.tag_index[tag_name] = TagNode(tag_name)
            tag = self.tag_index[tag_name]
            tag.notes.append(note)
            note.tags.append(tag)

        # simpan di note_index
        self.note_index[note.id] = note

        # catat ke circular buffer
        self._record_event(note, "create")

        print(f"[+] Note ditambahkan: {note}")
        return note

    # ── hapus note ──
    def delete_note(self, note_id: str):
        if note_id not in self.note_index:
            print(f"[!] Note id='{note_id}' tidak ditemukan.")
            return
        note = self.note_index.pop(note_id)

        # hapus dari kedua linked list
        self.chrono_list.remove(note)
        self.alpha_list.remove(note)

        # lepaskan dari semua tag
        for tag in note.tags:
            tag.notes = [n for n in tag.notes if n.id != note_id]

        self._record_event(note, "delete")
        print(f"[-] Note dihapus: id={note_id}, title='{note.title}'")

    # ── tampilkan semua note ──
    def view_chrono(self):
        print("\n📅  Chronological View:")
        for i, n in enumerate(self.chrono_list.to_list(), 1):
            print(f"  {i}. [{n.created_at.strftime('%H:%M:%S')}] {n.title} | tags={[t.name for t in n.tags]}")

    def view_alpha(self):
        print("\n🔤  Alphabetical View:")
        for i, n in enumerate(self.alpha_list.to_list(), 1):
            print(f"  {i}. {n.title} | tags={[t.name for t in n.tags]}")

    # ── cari note berdasarkan tag ──
    def find_by_tag(self, tag_name: str) -> list[NoteNode]:
        tag_name = tag_name.strip().lower()
        if tag_name not in self.tag_index:
            print(f"[!] Tag '{tag_name}' tidak ditemukan.")
            return []
        notes = self.tag_index[tag_name].notes
        print(f"\n🏷️  Notes dengan tag='{tag_name}':")
        for n in notes:
            print(f"  • {n.title} (id={n.id})")
        return notes

    # ── sync status ──
    def _record_event(self, note: NoteNode, action: str):
        note.sync_status = "pending"
        self.sync_buffer.push({
            "note_id":    note.id,
            "title":      note.title,
            "action":     action,
            "timestamp":  datetime.now().isoformat(),
            "sync_status": "pending"
        })

    def process_sync(self):
        """Simulasi memproses semua event pending di buffer."""
        print("\n🔄  Memproses sync buffer...")
        processed = 0
        while len(self.sync_buffer) > 0:
            event = self.sync_buffer.pop()
            if event and event["note_id"] in self.note_index:
                self.note_index[event["note_id"]].sync_status = "synced"
            print(f"  ✓ Synced: {event}")
            processed += 1
        print(f"  Total diproses: {processed} event(s)")

    def show_sync_buffer(self):
        print(f"\n📡  Sync Buffer: {self.sync_buffer}")


# ─────────────────────────────────────────────
#  DEMO / TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("   NOTE-TAKING APP — Demo Struktur Data")
    print("=" * 55)

    app = NoteApp(sync_buffer_size=5)

    # Tambah beberapa note
    n1 = app.add_note("Belajar Python",     "Materi OOP dan linked list",   ["kuliah", "penting"])
    n2 = app.add_note("Agenda Rapat",       "Besok pukul 09.00 WIB",        ["kerja", "penting"])
    n3 = app.add_note("Algoritma Sorting",  "Bubble, merge, quick sort",    ["kuliah"])
    n4 = app.add_note("Catatan Belanja",    "Beras, telur, minyak goreng",  ["pribadi"])
    n5 = app.add_note("Deadline Proyek",    "Submit sebelum Jumat",         ["kerja", "penting"])

    # View chronological & alphabetical
    app.view_chrono()
    app.view_alpha()

    # Cari berdasarkan tag
    app.find_by_tag("penting")
    app.find_by_tag("kuliah")

    # Tampilkan sync buffer sebelum diproses
    app.show_sync_buffer()

    # Proses sync
    app.process_sync()

    # Hapus salah satu note
    app.delete_note(n4.id)

    # Tampilkan ulang setelah hapus
    app.view_alpha()
    app.show_sync_buffer()
    app.process_sync()

    print("\n✅  Demo selesai.")
