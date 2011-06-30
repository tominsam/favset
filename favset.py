import logging

from config import config
from auth import FlickrBaseApp
from FlickrApp import FlickrAppAPIException


SET_TITLE="Your Favourites"


class Index(FlickrBaseApp):
    def __init__(self):
        super(Index,self).__init__()
        self.flickr_ttl = 1 # debugging


    def favset (self):
        # common stuff for get + post

        self.photosets = self.flickr("photosets.getList")[u'photosets'][u'photoset']
        # hack the response format to be usable from template
        for pset in self.photosets:
            pset["title"] = pset["title"]["_content"]
            
        # look for the photoset we're interested in
        set_id = self.request.get("photoset", None) # from form
        def is_your_favourites(pset):
            if set_id:
                return pset["id"] == set_id
            else:
                # find 'Your Favourites' set based on title
                return pset["title"] == SET_TITLE

        fav_sets = filter(is_your_favourites, self.photosets)
        if len(fav_sets) > 0:
            self.fav_set = fav_sets[0]
        else:
            self.fav_set = None
        
        logging.info("picked fav_set %r"%self.fav_set)

        try:
            self.popular = self.flickr("stats.getPopularPhotos", 
                sort='favorites',
                per_page=str(9*8) # makes a nice square on the sets page.
            )['photos']['photo']

        except FlickrAppAPIException, e:
            if e.value == "User does not have stats":
                self.render_error("You don't have stats enabled.", "Visit <a target='_blank' href='http://flickr.com/photos/me/stats/'>http://flickr.com/photos/me/stats/</a> to turn it on, then come back tomorrow.")
                return False
            else:
                raise

        return True


    def get(self):
        if not self.check_logged_in(self.min_perms) :
            return self.render("login.html")

        if not self.favset():
            return

        return self.render("index.html")

        

    def post(self):
        if not self.check_logged_in(self.min_perms) :
            return self.render("login.html")

        if not self.favset():
            return

        if not self.popular:
            return render_error("No-one loves you", "You have no photos favourited by other people. I can't make you a set. Sorry.")

        if not self.fav_set:
            # create set
            ret = self.flickr("photosets.create",
                title=SET_TITLE,
                primary_photo_id=self.popular[0]["id"]
            )
            set_id = ret["photoset"]["id"]
            primary = self.popular[0]["id"]

        else:
            set_id = self.fav_set["id"]
            primary = self.fav_set["primary"]

        # list of IDs for faves
        photo_id_list = [photo['id'] for photo in self.popular]
        
        # force sanity on primary photo id.
        if not primary in photo_id_list:
            primary = photo_id_list[0]

        photo_ids = ",".join(photo_id_list)

        # reorder set
        self.flickr("photosets.editPhotos",
            photoset_id=set_id,
            primary_photo_id=primary,
            photo_ids=photo_ids,
        )

        return self.redirect("http://www.flickr.com/photos/%s/sets/%s"%(self.user.nsid, set_id))

