import sys
import json
import subprocess
import threading
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QProgressBar, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, pyqtSlot

DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
}
QWidget {
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    color: #cdd6f4;
}
QLineEdit, QTextEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px;
    color: #cdd6f4;
}
QPushButton {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #a6adc8;
}
QTableWidget {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #45475a;
}
QHeaderView::section {
    background-color: #1e1e2e;
    color: #cdd6f4;
    padding: 4px;
    border: 1px solid #45475a;
    font-weight: bold;
}
QProgressBar {
    border: 1px solid #45475a;
    border-radius: 6px;
    text-align: center;
    background-color: #313244;
    color: #cdd6f4;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #a6e3a1;
    border-radius: 5px;
}
QTableWidget::item:selected {
    background-color: #585b70;
}
"""

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, sort_value):
        super().__init__(text)
        self.sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            try:
                return float(self.sort_value) < float(other.sort_value)
            except ValueError:
                return str(self.sort_value) < str(other.sort_value)
        return super().__lt__(other)

class WorkerSignals(QObject):
    formats_ready = pyqtSignal(str, list)
    error = pyqtSignal(str)
    progress_update = pyqtSignal(int, str)
    download_complete = pyqtSignal()
    
class YtDlpApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp GUI - Ultimate Downloader")
        self.resize(1100, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        
        self.url = ""
        self.signals = WorkerSignals()
        self.signals.formats_ready.connect(self.on_formats_ready)
        self.signals.error.connect(self.on_error)
        self.signals.progress_update.connect(self.on_progress_update)
        self.signals.download_complete.connect(self.on_download_complete)
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Top input row
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here...")
        self.fetch_btn = QPushButton("Fetch Formats")
        self.fetch_btn.clicked.connect(self.fetch_clicked)
        input_layout.addWidget(QLabel("Video URL:"))
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(self.fetch_btn)
        layout.addLayout(input_layout)
        
        # Tables using QSplitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Video Container
        vid_widget = QWidget()
        vid_layout = QVBoxLayout(vid_widget)
        vid_layout.setContentsMargins(0, 0, 0, 0)
        vid_layout.addWidget(QLabel("Select Video Stream:"))
        self.video_table = QTableWidget(0, 6)
        self.video_table.setHorizontalHeaderLabels(["ID", "Ext", "Resolution", "FPS", "Video Codec", "Size"])
        self.video_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.video_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.video_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vid_layout.addWidget(self.video_table)
        
        # Audio Container
        aud_widget = QWidget()
        aud_layout = QVBoxLayout(aud_widget)
        aud_layout.setContentsMargins(0, 0, 0, 0)
        aud_layout.addWidget(QLabel("Select Audio Stream:"))
        self.audio_table = QTableWidget(0, 5)
        self.audio_table.setHorizontalHeaderLabels(["ID", "Ext", "Audio Codec", "Bitrate (kbps)", "Size"])
        self.audio_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.audio_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.audio_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        aud_layout.addWidget(self.audio_table)
        
        splitter.addWidget(vid_widget)
        splitter.addWidget(aud_widget)
        layout.addWidget(splitter, 5)
        
        # Bottom Actions
        self.download_btn = QPushButton("Download and Merge")
        self.download_btn.clicked.connect(self.download_clicked)
        self.download_btn.setMinimumHeight(45)
        self.download_btn.setEnabled(False)
        layout.addWidget(self.download_btn)
        
        # Progress and Status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(25)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        layout.addWidget(self.status_label)
        
        # Logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area, 2)
        
        self.log("Ready. Paste a valid URL and click 'Fetch Formats'.")

    def log(self, text):
        self.log_area.append(text)
        # Auto scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def format_size(self, bytes_size):
        if not bytes_size:
            return "Unknown"
        bytes_size = float(bytes_size)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    def fetch_clicked(self):
        url = self.url_input.text().strip()
        if not url:
            self.log("Please enter a URL.")
            return
        
        self.url = url
        self.fetch_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.log(f"Fetching formats for: {url} ... (This may take a few seconds)")
        self.status_label.setText("Fetching format information...")
        self.progress_bar.setValue(0)
        
        threading.Thread(target=self._fetch_formats_thread, args=(url,), daemon=True).start()

    def _fetch_formats_thread(self, url):
        try:
            cmd = ['yt-dlp', '-J', url]
            # Use specific yt-dlp lookup to get json info
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                self.signals.error.emit(f"yt-dlp error:\n{stderr}")
                return
            
            info = json.loads(stdout)
            formats = info.get('formats', [])
            title = info.get('title', 'Unknown Title')
            
            self.signals.formats_ready.emit(title, formats)
        except Exception as e:
            self.signals.error.emit(f"Failed to fetch formats: {str(e)}")

    @pyqtSlot(str, list)
    def on_formats_ready(self, title, formats):
        self.log(f"Successfully fetched info for: {title}")
        self.status_label.setText("Formats loaded. Select streams and download.")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)
        
        self.video_table.setSortingEnabled(False)
        self.audio_table.setSortingEnabled(False)
        
        self.video_table.setRowCount(0)
        self.audio_table.setRowCount(0)
        
        videos = []
        audios = []
        
        for f in formats:
            # yt-dlp format extraction
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            # Categorize based on presence of streams
            if vcodec != 'none':
                videos.append(f)
            if acodec != 'none':
                audios.append(f)

        # Populate Video Group
        self.video_table.setRowCount(len(videos))
        for row, f in enumerate(videos):
            f_id = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            res = f.get('resolution', 'N/A')
            if res == 'audio only' or not res:
                res = f"{f.get('width', 0)}x{f.get('height', 0)}"
            fps = f.get('fps', 0)
            if fps is None: fps = 0
            vc = f.get('vcodec', 'N/A')
            
            size_bytes = f.get('filesize') or f.get('filesize_approx') or 0
            size_str = self.format_size(size_bytes)
            
            # Create sortable items
            id_item = QTableWidgetItem(str(f_id))
            ext_item = QTableWidgetItem(str(ext))
            
            width = f.get('width') or 0
            height = f.get('height') or 0
            res_item = NumericTableWidgetItem(str(res), width * height)
            
            fps_item = NumericTableWidgetItem(str(fps) + " fps", float(fps))
            vc_item = QTableWidgetItem(str(vc))
            size_item = NumericTableWidgetItem(size_str, float(size_bytes))
            
            items = [id_item, ext_item, res_item, fps_item, vc_item, size_item]
            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.video_table.setItem(row, col, item)

        # Populate Audio Group
        self.audio_table.setRowCount(len(audios))
        for row, f in enumerate(audios):
            f_id = f.get('format_id', 'N/A')
            ext = f.get('ext', 'N/A')
            ac = f.get('acodec', 'N/A')
            abr = f.get('abr', 0)
            if abr is None: abr = 0
            
            size_bytes = f.get('filesize') or f.get('filesize_approx') or 0
            size_str = self.format_size(size_bytes)
            
            id_item = QTableWidgetItem(str(f_id))
            ext_item = QTableWidgetItem(str(ext))
            ac_item = QTableWidgetItem(str(ac))
            abr_item = NumericTableWidgetItem(f"{abr} kbps", float(abr))
            size_item = NumericTableWidgetItem(size_str, float(size_bytes))

            items = [id_item, ext_item, ac_item, abr_item, size_item]
            for col, item in enumerate(items):
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.audio_table.setItem(row, col, item)
                
        # Enable sorting
        self.video_table.setSortingEnabled(True)
        self.audio_table.setSortingEnabled(True)

    def download_clicked(self):
        v_rows = self.video_table.selectedItems()
        a_rows = self.audio_table.selectedItems()
        
        if not v_rows or not a_rows:
            self.log("⚠️ Please select ONE video format and ONE audio format to merge.")
            return
            
        v_idx = v_rows[0].row()
        a_idx = a_rows[0].row()
        
        v_id = self.video_table.item(v_idx, 0).text()
        a_id = self.audio_table.item(a_idx, 0).text()
        
        self.fetch_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        
        log_msg = f"Starting download -> Video: {v_id} | Audio: {a_id}"
        self.log(log_msg)
        self.status_label.setText(log_msg)
        self.progress_bar.setValue(0)
        
        threading.Thread(target=self._download_thread, args=(self.url, v_id, a_id), daemon=True).start()

    def _download_thread(self, url, v_id, a_id):
        try:
            format_str = f"{v_id}+{a_id}"
            # Standard yt-dlp command using ffmpeg
            cmd = ['yt-dlp', '-f', format_str, '--merge-output-format', 'mkv', '--newline', url]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
            
            progress_pattern = re.compile(r'\[download\]\s+([\d\.]+)%')
            
            for line in proc.stdout:
                line_str = line.strip()
                if not line_str:
                    continue
                
                # Check for progress
                match = progress_pattern.search(line_str)
                if match:
                    percent = float(match.group(1))
                    self.signals.progress_update.emit(int(percent), line_str)
                else:
                    self.signals.progress_update.emit(-1, line_str)
            
            proc.wait()
            if proc.returncode == 0:
                self.signals.download_complete.emit()
            else:
                self.signals.error.emit(f"Download process failed with exit code: {proc.returncode}")
        except Exception as e:
            self.signals.error.emit(f"Exception during download: {str(e)}")

    @pyqtSlot(int, str)
    def on_progress_update(self, percent, text):
        if percent >= 0:
            self.progress_bar.setValue(percent)
            self.status_label.setText(text)
        else:
            self.log(text)

    @pyqtSlot()
    def on_download_complete(self):
        self.log("✅ Download and merge completed successfully!")
        self.status_label.setText("Done.")
        self.progress_bar.setValue(100)
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)

    @pyqtSlot(str)
    def on_error(self, err_msg):
        self.log(f"❌ Error: {err_msg}")
        self.status_label.setText("Error encountered.")
        self.fetch_btn.setEnabled(True)
        self.download_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Custom tweaks for styling polish
    app.setStyle("Fusion") 

    window = YtDlpApp()
    window.show()
    sys.exit(app.exec())
