# coding=utf-8
""" Constants for django-wikidata-api package. """

ALL_LANGUAGES = "[AUTO_LANGUAGE],en,fr,ar,be,bg,bn,ca,cs,da,de,el,en,es,et,fa,fi,he,hi,hu,hy,id,it,ja" \
                ",jv,ko,nb,nl,eo,pa,pl,pt,ro,ru,sh,sk,sr,sv,sw,te,th,tr,uk,yue,vec,vi,zh"
ENGLISH_LANG = "en"
WIKIDATA_ENTITY_PREFIX = "wd"
WIKIDATA_PROP_PREFIX = "wdt"
WIKIDATA_SUBCLASS_PROP = "P279"
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_ENTITY_PREFIX_URL = "http://www.wikidata.org/entity/"
WIKIDATA_PROP_PREFIX_URL = "http://www.wikidata.org/prop/direct/"
WIKIDATA_ENTITY_REGEX = r"([Qq])\d+"
WIKIDATA_PROP_REGEX = r"([Pp])\d+"
