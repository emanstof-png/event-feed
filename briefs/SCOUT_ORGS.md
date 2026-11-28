You are harvesting NAMES OF SMALL DC-AREA COMMUNITIES from event listings already saved in this repo.
Files only. Never WebFetch, WebSearch or browse. Never invent a name or URL.

Input: the files or row ranges in your task line (event listings from aggregators and from our own sources:
titles, descriptions, venues, "hosted by", "presented with", "in partnership with", organizer fields).

Extract every distinct ORGANIZING GROUP that:
- is a community, club, society, congregation, collective, studio, host series, chapter, network or small nonprofit
  that runs its own recurring events (not a one-off party name, not a performer, not a speaker);
- is plausibly in DC, Arlington, Alexandria, Bethesda, Silver Spring or nearby Maryland/Virginia.
Skip: big venues and arenas, restaurants and bars named only as venues, government agencies, national brands,
universities as a whole (a named university club/society is fine), and the source we already took it from.

OUTPUT: TSV to the path in your task line, header first:
Org<TAB>URL<TAB>Category<TAB>Evidence<TAB>Found in
- URL: only a URL printed in the file next to that group (organizer page, website, Meetup/Luma/Eventbrite organizer); else blank.
- Category: one of Jewish young adult / Meditation / Salons & discussion / Book & essay discussion / Alumni clubs /
  Young patrons & galas / Intimate music / Supper clubs & dinners / Language exchange / Crafts & cooking / Dance & social dance /
  Games & social play / Volunteer project teams / Spiritual & movement / Science & technology / Arts & culture / Other.
- Evidence: one event title (with date if shown) where the group appears, quoted briefly.
- Found in: the file name (and row number if given).
One row per group; if a group appears many times, keep one row and note "xN" at the end of Evidence.
Then reply exactly: done <rows>
