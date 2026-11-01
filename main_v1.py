import os
import sys
from ctypes import cast, POINTER

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


# =========================================================
# CẤU HÌNH
# =========================================================

VIDEO_NAME = "video.mp4"

# Âm lượng tổng Windows = 80%
WINDOWS_VOLUME = 0.80


# =========================================================
# LẤY THƯ MỤC CHƯƠNG TRÌNH
# =========================================================

def get_program_folder():
    """
    Lấy thư mục chứa file Python hoặc EXE.
    """

    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))


# =========================================================
# ĐẶT MASTER VOLUME WINDOWS = 80%
# =========================================================

def set_volume_80():
    """
    Đặt âm lượng tổng của Windows về 80%.
    Đồng thời bỏ mute nếu Windows đang tắt tiếng.
    """

    try:
        device = AudioUtilities.GetSpeakers()

        # Cách mới của pycaw
        try:
            volume = device.EndpointVolume

        # Fallback cho một số phiên bản pycaw cũ
        except Exception:
            interface = device.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )

            volume = cast(
                interface,
                POINTER(IAudioEndpointVolume)
            )

        # Bỏ mute
        volume.SetMute(0, None)

        # Master Volume = 80%
        volume.SetMasterVolumeLevelScalar(
            WINDOWS_VOLUME,
            None
        )

        # Đọc lại để kiểm tra
        current_volume = volume.GetMasterVolumeLevelScalar()

        # print(
        #     f"Âm lượng Windows hiện tại: "
        #     f"{round(current_volume * 100)}%"
        # )

        return True

    except Exception as e:

        print("\n==============================")
        print("LỖI CHỈNH ÂM LƯỢNG WINDOWS")
        print("==============================")
        print(repr(e))
        print()

        return False


# =========================================================
# TRÌNH PHÁT VIDEO
# =========================================================

class VideoWindow(QMainWindow):

    def __init__(self, video_path):
        super().__init__()

        self.video_path = video_path

        # -------------------------------------------------
        # Cửa sổ không có title bar / nút X
        # -------------------------------------------------

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setStyleSheet(
            "background-color: black;"
        )

        # Ẩn chuột
        self.setCursor(
            QCursor(Qt.CursorShape.BlankCursor)
        )

        # -------------------------------------------------
        # VIDEO WIDGET
        # -------------------------------------------------

        self.video_widget = QVideoWidget()

        self.video_widget.setStyleSheet(
            "background-color: black;"
        )

        self.video_widget.setCursor(
            QCursor(Qt.CursorShape.BlankCursor)
        )

        self.setCentralWidget(
            self.video_widget
        )

        # -------------------------------------------------
        # AUDIO
        # -------------------------------------------------

        self.audio_output = QAudioOutput()

        # Volume riêng của video = 100%
        # Master Volume Windows sẽ là 80%
        self.audio_output.setVolume(1.0)

        # -------------------------------------------------
        # MEDIA PLAYER
        # -------------------------------------------------

        self.player = QMediaPlayer()

        self.player.setAudioOutput(
            self.audio_output
        )

        self.player.setVideoOutput(
            self.video_widget
        )

        self.player.setSource(
            QUrl.fromLocalFile(
                self.video_path
            )
        )

        # -------------------------------------------------
        # EVENTS
        # -------------------------------------------------

        self.player.mediaStatusChanged.connect(
            self.media_status_changed
        )

        self.player.errorOccurred.connect(
            self.media_error
        )


    # =====================================================
    # BẮT ĐẦU
    # =====================================================

    def start(self):

        # Đặt volume trước khi phát
        set_volume_80()

        # Full màn hình
        self.showFullScreen()

        # Luôn nằm trên cùng
        self.raise_()
        self.activateWindow()

        # Phát video
        self.player.play()

        # Đặt lại volume sau khi player khởi tạo audio
        QTimer.singleShot(
            300,
            set_volume_80
        )

        # Đặt lại lần nữa sau 1 giây để chắc chắn
        QTimer.singleShot(
            1000,
            set_volume_80
        )


    # =====================================================
    # VIDEO CHẠY XONG
    # =====================================================

    def media_status_changed(self, status):

        if status == QMediaPlayer.MediaStatus.EndOfMedia:

            self.player.stop()

            QApplication.quit()


    # =====================================================
    # LỖI VIDEO
    # =====================================================

    def media_error(self, error, error_string):

        if error != QMediaPlayer.Error.NoError:

            print()
            print("==============================")
            print("LỖI PHÁT VIDEO")
            print("==============================")
            print(error_string)

            QMessageBox.critical(
                self,
                "Lỗi phát video",
                f"Không thể phát video.\n\n"
                f"Lỗi:\n{error_string}"
            )

            QApplication.quit()


    # =====================================================
    # ESC = THOÁT KHẨN CẤP
    # =====================================================

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_Escape:

            self.player.stop()

            QApplication.quit()

            return

        super().keyPressEvent(event)


# =========================================================
# MAIN
# =========================================================

def main():

    folder = get_program_folder()

    video_path = os.path.join(
        folder,
        VIDEO_NAME
    )

    # -----------------------------------------------------
    # KHỞI TẠO QT
    # -----------------------------------------------------

    app = QApplication(sys.argv)

    # -----------------------------------------------------
    # KIỂM TRA VIDEO
    # -----------------------------------------------------

    if not os.path.isfile(video_path):

        QMessageBox.critical(
            None,
            "Không tìm thấy video",
            f"Không tìm thấy file:\n\n"
            f"{video_path}\n\n"
            f"Hãy đặt file {VIDEO_NAME} "
            f"cùng thư mục với hi.py."
        )

        sys.exit(1)

    # -----------------------------------------------------
    # ĐẶT WINDOWS VOLUME = 80%
    # -----------------------------------------------------

    set_volume_80()

    # -----------------------------------------------------
    # MỞ VIDEO
    # -----------------------------------------------------

    window = VideoWindow(
        video_path
    )

    window.start()

    sys.exit(
        app.exec()
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()