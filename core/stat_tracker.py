from terminaltables import AsciiTable


class StatTracker:

    __downloaded_photo: int = 0
    __passed_photo: int = 0
    __error_photo: int = 0

    __downloaded_video: int = 0
    __passed_video: int = 0
    __error_video: int = 0

    __downloaded_audio: int = 0
    __passed_audio: int = 0
    __error_audio: int = 0

    __downloaded_file: int = 0
    __passed_file: int = 0
    __error_file: int = 0

    total_photos: int = 0
    total_videos: int = 0
    total_audios: int = 0

    __download_errors: list = []

    def add_downloaded_photo(self):
        self.__downloaded_photo += 1

    def add_downloaded_video(self):
        self.__downloaded_video += 1

    def add_downloaded_audio(self):
        self.__downloaded_audio += 1

    def add_downloaded_file(self):
        self.__downloaded_file += 1

    def add_passed_photo(self):
        self.__passed_photo += 1

    def add_passed_video(self):
        self.__passed_video += 1

    def add_passed_audio(self):
        self.__passed_audio += 1

    def add_passed_file(self):
        self.__passed_file += 1

    def add_error_photo(self):
        self.__error_photo += 1

    def add_error_video(self):
        self.__error_video += 1

    def add_error_audio(self):
        self.__error_audio += 1

    def add_error_file(self):
        self.__error_file += 1

    def add_download_error(self, file_url: str):
        self.__download_errors.append(file_url)

    def __str__(self):
        photo_stat = [
            ['Photo Stat', 'Value'],
            ['TOTAL', self.total_photos],
            ['DOWNLOADED', self.__downloaded_photo],
            ['PASSED DUE FOUND', self.__passed_photo],
            ['PASSED DUE ERROR', self.__error_photo],
        ]
        photo_table = AsciiTable(photo_stat)

        video_stat = [
            ['Video Stat', 'Value'],
            ['TOTAL', self.total_videos],
            ['DOWNLOADED', self.__downloaded_video],
            ['PASSED DUE FOUND', self.__passed_video],
            ['PASSED DUE ERROR', self.__error_video],
        ]
        video_table = AsciiTable(video_stat)

        audio_stat = [
            ['Audio Stat', 'Value'],
            ['TOTAL', self.total_audios],
            ['DOWNLOADED', self.__downloaded_audio],
            ['PASSED DUE FOUND', self.__passed_audio],
            ['PASSED DUE ERROR', self.__error_audio],
        ]
        audio_table = AsciiTable(audio_stat)

        file_stat = [
            ['File Stat', 'Value'],
            ['DOWNLOADED', self.__downloaded_file],
            ['PASSED DUE FOUND', self.__passed_file],
            ['PASSED DUE ERROR', self.__error_file],
        ]
        file_table = AsciiTable(file_stat)

        result = (
                str(photo_table.table) + "\n\n" +
                str(video_table.table) + "\n\n" +
                str(audio_table.table) + "\n\n" +
                str(file_table.table) + "\n\n"
        )
        if len(self.__download_errors):
            result += "\n\nWARNING: Downloading of some files failed!\n"
            result += "The following are the files that have not been downloaded for any reason:\n"
            result += "\n".join(self.__download_errors) + "\n\n"
            result += "Download it manually or start syncing again."
        return result

    def show_summary(self):
        print("\n\n" + self.__str__())


""" 
Singleton only!
"""
stat_tracker = StatTracker()
