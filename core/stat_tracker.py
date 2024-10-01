from terminaltables import AsciiTable


class StatTracker:

    __downloaded_photo: int = 0
    __passed_photo: int = 0

    __downloaded_video: int = 0
    __passed_video: int = 0

    total_photos: int = 0
    total_videos: int = 0

    __download_errors: list = []

    def add_downloaded_photo(self):
        self.__downloaded_photo += 1

    def add_downloaded_video(self):
        self.__downloaded_video += 1

    def add_passed_photo(self):
        self.__passed_photo += 1

    def add_passed_video(self):
        self.__passed_video += 1

    def add_download_error(self, file_url: str):
        self.__download_errors.append(file_url)

    def __str__(self):
        photo_stat = [
            ['Photo Stat', 'Value'],
            ['TOTAL', self.total_photos],
            ['DOWNLOADED', self.__downloaded_photo],
            ['COLLECTED IN LOCAL FILES', self.__passed_photo + self.__downloaded_photo],
            ['NOT DOWNLOADED', self.total_photos - (self.__passed_photo + self.__downloaded_photo)],
        ]
        photo_table = AsciiTable(photo_stat)

        video_stat = [
            ['Video Stat', 'Value'],
            ['TOTAL', self.total_videos],
            ['DOWNLOADED', self.__downloaded_video],
            ['COLLECTED IN LOCAL FILES', self.__passed_video + self.__downloaded_video],
            ['NOT DOWNLOADED', self.total_videos - (self.__passed_video + self.__downloaded_video)],
        ]
        video_table = AsciiTable(video_stat)

        result = str(photo_table.table) + "\n\n" + str(video_table.table)
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
