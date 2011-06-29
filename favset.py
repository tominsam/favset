import logging

from config import config
from auth import FlickrBaseApp
from FlickrApp import FlickrAppAPIException


SET_TITLE="Your Favourites"


class Index(FlickrBaseApp):
    def __init__(self):
        super(Index,self).__init__()
        self.flickr_ttl = 120


    def get (self) :
        if not self.check_logged_in(self.min_perms) :
            return self.render("login.html", locals())

        photosets = self.flickr("photosets.getList")[u'photosets'][u'photoset']
        logging.info("sets are %r"%photosets)
        
        def is_your_favourites(set):
            return set["title"]["_content"] == SET_TITLE
        fav_sets = filter(is_your_favourites, photosets)
        if len(fav_sets) > 0:
            fav_set = fav_sets[0]
        else:
            fav_set = None
        logging.info("Found favourites set %r"%fav_set)

        try:
            popular = self.flickr("stats.getPopularPhotos", 
                sort='favorites',
                per_page=str(9*8) # makes a nice square on the sets page.
            )['photos']['photo']

        except FlickrAppAPIException, e:
            if e.value == "User does not have stats":
                return self.render_error("You don't have stats enabled.", "Visit <a target='_blank' href='http://flickr.com/photos/me/stats/'>http://flickr.com/photos/me/stats/</a>")
            else:
                raise
        logging.info("popular is %r"%popular)

        photo_id_list = [photo['id'] for photo in popular]
        photo_ids = ",".join(photo_id_list)

        if self.POST.get("doit", None):
            if not photos:
                return render_error("Noone loves you", "You have no photos favourited by other people.")

            if not fav_set:
                # create set
                ret = self.flickr("photosets.create",
                    title=SET_TITLE,
                    primary_photo_id=photos[0]["id"]
                )
                set_id = ret["id"]
                primary = photos[0]["id"]

            else:
                set_id = fav_set["id"]
                primary = fav_st["primary"]

            # reorder set
            self.flickr("photosets.editPhotos",
                photoset_id=set_id,
                primary_photo_id=primary,
                photo_ids=photo_ids,
            )

            return self.redirect("http://www.flickr.com/photos/%s/sets/%s"%(self.user.id, set_id))


        return self.render("index.html", locals())
    
