class BeatmapSet:
    def __init__(self, **kwargs):
        self.id = ""
        self.title = ""
        self.artist = ""
        self.status = ""
        self.favourite_count = ""

    def build_from_query(self, qdict):
        self.title = qdict['title']
        self.id = str(qdict['id'])
        self.artist = qdict['artist']
        self.status = qdict['status']
        self.favourite_count = qdict['favourite_count']
        return self

    def add_status(self, status):
        if status == 1:
            self.status = "Ranked"
        elif status == 3:
            self.status = "Qualified"
        else:
            self.status = "Unranked"

    def print_info(self):
        print(self.artist + " -- " + self.title)
        print("ID: " + str(self.id))
        print("Status: " + self.status)
        print("Favourites: " + str(self.favourite_count))

    def export_string(self):
        str_repr = ""
        str_repr += str(self.id)
        str_repr += "||" + self.title + "||" + self.artist
        str_repr += "||" + str(self.status)
        str_repr += "||" + str(self.favourite_count)
        return str_repr
