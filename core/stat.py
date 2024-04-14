
class Stat:

    __downloaded_photo: int = 0
    __passed_photo: int = 0

    __downloaded_video: int = 0
    __passed_video: int = 0

    total_photos: int = 0
    total_videos: int = 0

    def add_downloaded_photo(self):
        self.__downloaded_photo += 1

    def add_downloaded_video(self):
        self.__downloaded_video += 1

    def add_passed_photo(self):
        self.__passed_photo += 1

    def add_passed_video(self):
        self.__passed_video += 1

    def __str__(self):
        return f"""
        \rTOTAL PHOTOS: {self.total_photos}
        \rDOWNLOADED PHOTOS: {self.__downloaded_photo}
        \rPHOTOS COLLECTED IN LOCAL FILES: {self.__passed_photo + self.__downloaded_photo}
        \rPHOTOS UNAVAILABLE: {self.total_photos - (self.__passed_photo + self.__downloaded_photo)}
        
        \rTOTAL VIDEOS: {self.total_videos}
        \rDOWNLOADED VIDEOS: {self.__downloaded_video}
        \rVIDEOS COLLECTED IN LOCAL FILES: {self.__passed_video + self.__downloaded_video}
        \rVIDEOS UNAVAILABLE: {self.total_videos - (self.__passed_video + self.__downloaded_video)}
        """


stat_tracker = Stat()
