#!/usr/bin/env python3
"""Scrape name data from Kate Monk's Onomastikon (tekeli.li).

Produces three files in data/:
    male_first.txt    — male first names
    female_first.txt  — female first names
    surnames.txt      — surnames

All page paths are hardcoded for efficiency and reproducibility.
Uses only the Python standard library. Includes polite rate-limiting.

Source: https://tekeli.li/onomastikon/
© 1997 Kate Monk
"""

import os
import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser

BASE_URL = "https://tekeli.li/onomastikon/"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Delay between HTTP requests (seconds)
REQUEST_DELAY = 0.3

# ---------------------------------------------------------------------------
# Page lists — every page we want, classified by type
# ---------------------------------------------------------------------------

# Pages containing exclusively male first names
MALE_PAGES = [
    "Ancient-World/Egypt/Male.html",
    "Ancient-World/Greece/Male.html",
    "Celtic/Brittany/Male.html",
    "Celtic/Celtic/Male.html",
    "Celtic/Ireland/Celtic-Male.html",
    "Celtic/Wales/Celtic-Male.html",
    "England-Firstnames/African-American/American-Male.html",
    "England-Firstnames/African-American/Arabic-Male.html",
    "England-Firstnames/African-American/Inventions-Male.html",
    "England-Firstnames/Surname-Adaptations/English-Male-A-C.html",
    "England-Firstnames/Surname-Adaptations/English-Male-D-J.html",
    "England-Firstnames/Surname-Adaptations/English-Male-K-R.html",
    "England-Firstnames/Surname-Adaptations/English-Male-S-Z.html",
    "England-Firstnames/Variants/Biblical-Male-NT.html",
    "England-Firstnames/Variants/Biblical-Male-OT.html",
    "England-Firstnames/Variants/Celtic-Male.html",
    "England-Firstnames/Variants/Germanic-Male.html",
    "England-Firstnames/Variants/Greek-Male.html",
    "England-Firstnames/Variants/Latin-Male.html",
    "Europe-Eastern/Albania/Male.html",
    "Europe-Eastern/Former-Yugoslavia/Slovenia/Male.html",
    "Europe-Eastern/Romania/Male.html",
    "Europe-Scandinavia/Old-Norse/Male.html",
    "Europe-Western/Basque/Male.html",
    "India/Hindu-Names/Male-a.html",
    "India/Hindu-Names/Male-b.html",
    "India/Hindu-Names/Male-c-k.html",
    "India/Hindu-Names/Male-l-z.html",
    "Middle-East/Arab/Male.html",
    "Orient/China/Male.html",
    "Orient/Japan/Male.html",
    "Orient/Korea/Male.html",
]

# Pages containing exclusively female first names
FEMALE_PAGES = [
    "Ancient-World/Egypt/Female.html",
    "Ancient-World/Greece/Female.html",
    "Celtic/Brittany/Female.html",
    "Celtic/Celtic/Female.html",
    "Celtic/Ireland/Celtic-Female.html",
    "Celtic/Wales/Celtic-Female.html",
    "England-Firstnames/African-American/American-Female.html",
    "England-Firstnames/African-American/Arabic-Female.html",
    "England-Firstnames/African-American/Inventions-Female.html",
    "England-Firstnames/Surname-Adaptations/English-Female.html",
    "England-Firstnames/Variants/Biblical-Female-NT.html",
    "England-Firstnames/Variants/Biblical-Female-OT.html",
    "England-Firstnames/Variants/Celtic-Female.html",
    "England-Firstnames/Variants/Germanic-Female.html",
    "England-Firstnames/Variants/Greek-Female.html",
    "England-Firstnames/Variants/Latin-Female.html",
    # Linknames are feminine adaptations of male names
    "England-Firstnames/Linknames/Biblical.html",
    "England-Firstnames/Linknames/Celtic.html",
    "England-Firstnames/Linknames/Germanic.html",
    "England-Firstnames/Linknames/Greek.html",
    "England-Firstnames/Linknames/Latin.html",
    "Europe-Eastern/Albania/Female.html",
    "Europe-Eastern/Former-Yugoslavia/Slovenia/Female.html",
    "Europe-Eastern/Romania/Female.html",
    "Europe-Scandinavia/Old-Norse/Female.html",
    "Europe-Western/Basque/Female.html",
    "India/Hindu-Names/Female.html",
    "Middle-East/Arab/Female.html",
    "Orient/China/Female.html",
    "Orient/Japan/Female.html",
    "Orient/Korea/Female.html",
]

# Pages containing surnames
SURNAME_PAGES = [
    # Celtic
    "Celtic/Brittany/Surnames.html",
    "Celtic/Ireland/Surnames-A-F.html",
    "Celtic/Ireland/Surnames-G-Mac.html",
    "Celtic/Ireland/Surnames-M-Z.html",
    "Celtic/Scotland/Surnames.html",
    "Celtic/Wales/Surnames.html",
    # England
    "England-Surnames/Byname.html",
    "England-Surnames/Localities.html",
    "England-Surnames/Matronymics.html",
    "England-Surnames/Old-English.html",
    "England-Surnames/Patronymics.html",
    "England-Surnames/Tradenames.html",
    # Europe Western
    "Europe-Western/Austria/Surnames.html",
    "Europe-Western/Basque/Surnames.html",
    "Europe-Western/Belgium/Surnames.html",
    "Europe-Western/France/Surnames.html",
    "Europe-Western/Germany/Surnames.html",
    "Europe-Western/Italy/Surnames.html",
    "Europe-Western/Netherlands/Surnames.html",
    "Europe-Western/Portugal/Surnames.html",
    "Europe-Western/Spain/Surnames.html",
    "Europe-Western/Switzerland/Surnames.html",
    # Europe Eastern
    "Europe-Eastern/Czech-Slovak/Surnames-Czech.html",
    "Europe-Eastern/Czech-Slovak/Surnames-Czechoslovakia.html",
    "Europe-Eastern/Czech-Slovak/Surnames-Slovak.html",
    "Europe-Eastern/Greece/Surnames.html",
    "Europe-Eastern/Hungary/Surnames.html",
    "Europe-Eastern/Poland/Surnames.html",
    # Scandinavia
    "Europe-Scandinavia/Denmark/Surnames.html",
    "Europe-Scandinavia/Finland/Surnames.html",
    "Europe-Scandinavia/Norway/Surnames.html",
    "Europe-Scandinavia/Sweden/Surnames.html",
]

# Pages with both male and female names (divided by section headings)
MIXED_PAGES = [
    # Celtic
    "Celtic/Celtic/Cornwall.html",
    "Celtic/Celtic/Manx.html",
    "Celtic/Ireland/Biblical.html",
    "Celtic/Ireland/Germanic.html",
    "Celtic/Ireland/Greek.html",
    "Celtic/Ireland/Latin.html",
    "Celtic/Ireland/Religious.html",
    "Celtic/Scotland/Biblical.html",
    "Celtic/Scotland/Celtic.html",
    "Celtic/Scotland/Germanic.html",
    "Celtic/Scotland/Greek.html",
    "Celtic/Scotland/Latin.html",
    "Celtic/Scotland/Norse.html",
    "Celtic/Scotland/Religious.html",
    "Celtic/Wales/Biblical.html",
    "Celtic/Wales/Germanic.html",
    "Celtic/Wales/Greek.html",
    "Celtic/Wales/Latin.html",
    # England Saxon & Medieval
    "England-Saxon/Dithematic.html",
    "England-Saxon/Monothematic.html",
    "England-Medieval/Biblical.html",
    "England-Medieval/Celtic.html",
    "England-Medieval/Early-Modern.html",
    "England-Medieval/Greek.html",
    "England-Medieval/Latin.html",
    "England-Medieval/Norman.html",
    "England-Medieval/Norse.html",
    "England-Medieval/Puritan.html",
    "England-Medieval/Rarities.html",
    "England-Medieval/Saxon.html",
    # England Firstnames — mixed sub-pages
    "England-Firstnames/African-American/African.html",
    "England-Firstnames/African-American/Various.html",
    "England-Firstnames/Coinages/Blended.html",
    "England-Firstnames/Coinages/Borrowed-Words.html",
    "England-Firstnames/Coinages/Combined.html",
    "England-Firstnames/Coinages/Suffix.html",
    "England-Firstnames/Coinages/Unisex.html",
    "England-Firstnames/Foreign/French.html",
    "England-Firstnames/Foreign/German.html",
    "England-Firstnames/Foreign/Hindu.html",
    "England-Firstnames/Foreign/Italian.html",
    "England-Firstnames/Foreign/Norse.html",
    "England-Firstnames/Foreign/Slavic.html",
    "England-Firstnames/Foreign/Spanish.html",
    "England-Firstnames/Foreign/Various.html",
    "England-Firstnames/Literary/Arthurian.html",
    "England-Firstnames/Literary/Chaucer.html",
    "England-Firstnames/Literary/Mitchell.html",
    "England-Firstnames/Literary/Ossian.html",
    "England-Firstnames/Literary/Shakespeare.html",
    "England-Firstnames/Literary/Tolkien.html",
    "England-Firstnames/Surname-Adaptations/Foreign.html",
    "England-Firstnames/Surname-Adaptations/Irish.html",
    "England-Firstnames/Surname-Adaptations/Scottish.html",
    "England-Firstnames/Surname-Adaptations/Welsh.html",
    "England-Firstnames/Themes/Colours.html",
    "England-Firstnames/Themes/Creatures.html",
    "England-Firstnames/Themes/Dates.html",
    "England-Firstnames/Themes/Film-TV.html",
    "England-Firstnames/Themes/Flowers.html",
    "England-Firstnames/Themes/Jewels.html",
    "England-Firstnames/Themes/Letters.html",
    "England-Firstnames/Themes/Numbers.html",
    "England-Firstnames/Themes/Titles.html",
    "England-Firstnames/Themes/Twins.html",
    "England-Firstnames/Themes/Virtues.html",
    "England-Firstnames/Variants/Biblical-Patriarchs.html",
    "England-Firstnames/Variants/Biblical-Prophets.html",
    "England-Firstnames/Variants/Biblical-Rare.html",
    # England Firstnames — Austria/Switzerland first names
    "Europe-Western/Austria/Firstnames.html",
    "Europe-Western/Switzerland/Firstnames.html",
    # England Colonies
    "England-Colonies/Commonwealth.html",
    "England-Colonies/England-Counties.html",
    "England-Colonies/Mayflower.html",
    "England-Colonies/Pitcairn.html",
    "England-Colonies/United-States.html",
    "England-Colonies/West-Indies.html",
    # Europe Medieval
    "Europe-Medieval/Byzantium.html",
    "Europe-Medieval/France.html",
    "Europe-Medieval/Franks.html",
    "Europe-Medieval/Germany.html",
    "Europe-Medieval/Goths.html",
    "Europe-Medieval/Huns.html",
    "Europe-Medieval/Italy.html",
    "Europe-Medieval/Lombards.html",
    "Europe-Medieval/Roland.html",
    "Europe-Medieval/Romany.html",
    # Europe Western — thematic pages
    "Europe-Western/Belgium/Biblical.html",
    "Europe-Western/Belgium/Celtic.html",
    "Europe-Western/Belgium/Germanic.html",
    "Europe-Western/Belgium/Greek.html",
    "Europe-Western/Belgium/Latin.html",
    "Europe-Western/Belgium/Walloon.html",
    "Europe-Western/France/Biblical.html",
    "Europe-Western/France/Combined.html",
    "Europe-Western/France/Germanic.html",
    "Europe-Western/France/Greek.html",
    "Europe-Western/France/Languedoc.html",
    "Europe-Western/France/Latin.html",
    "Europe-Western/France/Provence.html",
    "Europe-Western/France/Various.html",
    "Europe-Western/Germany/Biblical.html",
    "Europe-Western/Germany/Germanic.html",
    "Europe-Western/Germany/Greek.html",
    "Europe-Western/Germany/Latin.html",
    "Europe-Western/Germany/Low-German.html",
    "Europe-Western/Germany/Various.html",
    "Europe-Western/Italy/Biblical.html",
    "Europe-Western/Italy/Germanic.html",
    "Europe-Western/Italy/Greek.html",
    "Europe-Western/Italy/Latin.html",
    "Europe-Western/Italy/Various.html",
    "Europe-Western/Netherlands/Biblical.html",
    "Europe-Western/Netherlands/Friesland.html",
    "Europe-Western/Netherlands/Germanic.html",
    "Europe-Western/Netherlands/Greek.html",
    "Europe-Western/Netherlands/Latin.html",
    "Europe-Western/Netherlands/Various.html",
    "Europe-Western/Portugal/Biblical.html",
    "Europe-Western/Portugal/Germanic.html",
    "Europe-Western/Portugal/Greek.html",
    "Europe-Western/Portugal/Latin.html",
    "Europe-Western/Portugal/Various.html",
    "Europe-Western/SmallStates/Andorra.html",
    "Europe-Western/SmallStates/Liechtenstein.html",
    "Europe-Western/SmallStates/Luxembourg.html",
    "Europe-Western/SmallStates/Malta.html",
    "Europe-Western/SmallStates/Monaco.html",
    "Europe-Western/Spain/Aragon.html",
    "Europe-Western/Spain/Asturias.html",
    "Europe-Western/Spain/Biblical.html",
    "Europe-Western/Spain/Catalonia.html",
    "Europe-Western/Spain/Galicia.html",
    "Europe-Western/Spain/Germanic.html",
    "Europe-Western/Spain/Greek.html",
    "Europe-Western/Spain/Latin.html",
    "Europe-Western/Spain/Various.html",
    # Europe Eastern — thematic pages
    "Europe-Eastern/Czech-Slovak/Biblical.html",
    "Europe-Eastern/Czech-Slovak/Germanic.html",
    "Europe-Eastern/Czech-Slovak/Greek.html",
    "Europe-Eastern/Czech-Slovak/Latin.html",
    "Europe-Eastern/Czech-Slovak/Slavic.html",
    "Europe-Eastern/Greece/Biblical.html",
    "Europe-Eastern/Greece/Cyprus.html",
    "Europe-Eastern/Greece/Germanic.html",
    "Europe-Eastern/Greece/Greek.html",
    "Europe-Eastern/Greece/Latin.html",
    "Europe-Eastern/Hungary/Biblical.html",
    "Europe-Eastern/Hungary/Germanic.html",
    "Europe-Eastern/Hungary/Greek.html",
    "Europe-Eastern/Hungary/Hungarian.html",
    "Europe-Eastern/Hungary/Latin.html",
    "Europe-Eastern/Hungary/Slavic.html",
    "Europe-Eastern/Poland/Biblical.html",
    "Europe-Eastern/Poland/Germanic.html",
    "Europe-Eastern/Poland/Greek.html",
    "Europe-Eastern/Poland/Latin.html",
    "Europe-Eastern/Poland/Slavonic.html",
    "Europe-Eastern/Poland/Various.html",
    # Europe Scandinavia — thematic pages
    "Europe-Scandinavia/Denmark/Biblical.html",
    "Europe-Scandinavia/Denmark/Germanic.html",
    "Europe-Scandinavia/Denmark/Greek.html",
    "Europe-Scandinavia/Denmark/Latin.html",
    "Europe-Scandinavia/Denmark/Norse.html",
    "Europe-Scandinavia/Denmark/Various.html",
    "Europe-Scandinavia/Faroes/Foreign.html",
    "Europe-Scandinavia/Faroes/Norse.html",
    "Europe-Scandinavia/Finland/Biblical.html",
    "Europe-Scandinavia/Finland/Compounds.html",
    "Europe-Scandinavia/Finland/Finnish.html",
    "Europe-Scandinavia/Finland/Various.html",
    "Europe-Scandinavia/Iceland/Biblical.html",
    "Europe-Scandinavia/Iceland/Germanic.html",
    "Europe-Scandinavia/Iceland/Greek.html",
    "Europe-Scandinavia/Iceland/Latin.html",
    "Europe-Scandinavia/Iceland/Norse.html",
    "Europe-Scandinavia/Iceland/Various.html",
    "Europe-Scandinavia/Norway/Biblical.html",
    "Europe-Scandinavia/Norway/Germanic.html",
    "Europe-Scandinavia/Norway/Greek.html",
    "Europe-Scandinavia/Norway/Latin.html",
    "Europe-Scandinavia/Norway/Norse.html",
    "Europe-Scandinavia/Norway/Various.html",
    "Europe-Scandinavia/Sweden/Biblical.html",
    "Europe-Scandinavia/Sweden/Germanic.html",
    "Europe-Scandinavia/Sweden/Greek.html",
    "Europe-Scandinavia/Sweden/Latin.html",
    "Europe-Scandinavia/Sweden/Norse.html",
    "Europe-Scandinavia/Sweden/Various.html",
    # Former Soviet Union
    "Former-Soviet-Union/Asia/Kazakhstan.html",
    "Former-Soviet-Union/Asia/Kirghizstan.html",
    "Former-Soviet-Union/Asia/Tajikhistan.html",
    "Former-Soviet-Union/Asia/Turkmenistan.html",
    "Former-Soviet-Union/Asia/Uzbekistan.html",
    "Former-Soviet-Union/Baltic/Estonia.html",
    "Former-Soviet-Union/Baltic/Latvia.html",
    "Former-Soviet-Union/Baltic/Lithuania.html",
    "Former-Soviet-Union/Europe_Caucasus/Armenia.html",
    "Former-Soviet-Union/Europe_Caucasus/Azerbaijan.html",
    "Former-Soviet-Union/Europe_Caucasus/Belarus.html",
    "Former-Soviet-Union/Europe_Caucasus/Caucasus.html",
    "Former-Soviet-Union/Europe_Caucasus/Georgia.html",
    "Former-Soviet-Union/Europe_Caucasus/Moldavia.html",
    "Former-Soviet-Union/Europe_Caucasus/Ukraine.html",
    "Former-Soviet-Union/Russia/Biblical.html",
    "Former-Soviet-Union/Russia/Germanic.html",
    "Former-Soviet-Union/Russia/Greek.html",
    "Former-Soviet-Union/Russia/Latin.html",
    "Former-Soviet-Union/Russia/Republics.html",
    "Former-Soviet-Union/Russia/Slavic.html",
    "Former-Soviet-Union/Russia/Various.html",
    # Ancient World
    "Ancient-World/Eastern/Ancient-Civilizations.html",
    "Ancient-World/Eastern/Assyria.html",
    "Ancient-World/Eastern/Babylon.html",
    "Ancient-World/Eastern/Hittites.html",
    "Ancient-World/Eastern/Palestine.html",
    "Ancient-World/Eastern/Persia.html",
    "Ancient-World/Eastern/Phoenicia.html",
    "Ancient-World/Eastern/Sumeria.html",
    "Ancient-World/Greece/Anatolia.html",
    "Ancient-World/Greece/Hellenic.html",
    "Ancient-World/Rome/Cognomina.html",
    "Ancient-World/Rome/Nomina.html",
    "Ancient-World/Rome/Praenomina.html",
    # Africa
    "Africa/Ancient/Aethiopia.html",
    "Africa/Ancient/Cyrenaica.html",
    "Africa/Ancient/Libya.html",
    "Africa/Ancient/Mauretania.html",
    "Africa/Ancient/Nubia.html",
    "Africa/Ancient/Numidia.html",
    "Africa/Central/Cameroon.html",
    "Africa/Central/Central-African-Republic.html",
    "Africa/Central/Central.html",
    "Africa/Central/Chad.html",
    "Africa/Central/Congo.html",
    "Africa/Central/Equatorial-Guinea.html",
    "Africa/Central/Gabon.html",
    "Africa/Central/Zaire.html",
    "Africa/Eastern/Burundi.html",
    "Africa/Eastern/Djibouti.html",
    "Africa/Eastern/Eastern.html",
    "Africa/Eastern/Eritrea.html",
    "Africa/Eastern/Ethiopia.html",
    "Africa/Eastern/Kenya.html",
    "Africa/Eastern/Rwanda.html",
    "Africa/Eastern/Somalia.html",
    "Africa/Eastern/Sudan.html",
    "Africa/Eastern/Swahili.html",
    "Africa/Eastern/Tanzania.html",
    "Africa/Eastern/Uganda.html",
    "Africa/Islands/Cape-Verde.html",
    "Africa/Islands/Comoros.html",
    "Africa/Islands/Madagascar.html",
    "Africa/Islands/Mauritius.html",
    "Africa/Islands/Sao-Tome-Principe.html",
    "Africa/Islands/Seychelles.html",
    "Africa/Northern/Algeria.html",
    "Africa/Northern/Egypt.html",
    "Africa/Northern/Libya.html",
    "Africa/Northern/Morocco.html",
    "Africa/Northern/Northern.html",
    "Africa/Northern/Tunisia.html",
    "Africa/Northern/Western-Sahara.html",
    "Africa/Southern/Angola.html",
    "Africa/Southern/Botswana.html",
    "Africa/Southern/Lesotho.html",
    "Africa/Southern/Malawi.html",
    "Africa/Southern/Mozambique.html",
    "Africa/Southern/Namibia.html",
    "Africa/Southern/South-Africa.html",
    "Africa/Southern/Southern.html",
    "Africa/Southern/Swaziland.html",
    "Africa/Southern/Zambia.html",
    "Africa/Southern/Zimbabwe.html",
    "Africa/Western/Benin.html",
    "Africa/Western/Burkina-Fasu.html",
    "Africa/Western/Gambia.html",
    "Africa/Western/Ghana.html",
    "Africa/Western/Guinea-Bissau.html",
    "Africa/Western/Guinea.html",
    "Africa/Western/Ivory-Coast.html",
    "Africa/Western/Liberia.html",
    "Africa/Western/Mali.html",
    "Africa/Western/Mauritania.html",
    "Africa/Western/Niger.html",
    "Africa/Western/Nigeria.html",
    "Africa/Western/Senegal.html",
    "Africa/Western/Sierra-Leone.html",
    "Africa/Western/Togo.html",
    "Africa/Western/Western.html",
    # America
    "America/North/Algonquin.html",
    "America/North/Apache.html",
    "America/North/Cherokee.html",
    "America/North/Choctaw.html",
    "America/North/Creek.html",
    "America/North/Crow.html",
    "America/North/Hopi.html",
    "America/North/Inuit.html",
    "America/North/Iroquois.html",
    "America/North/Kiowa.html",
    "America/North/Miwok.html",
    "America/North/Nations.html",
    "America/North/Native.html",
    "America/North/Navajo.html",
    "America/North/Nez-Perce.html",
    "America/North/Ojibwa.html",
    "America/North/Omaha.html",
    "America/North/Osage.html",
    "America/North/Seminole.html",
    "America/North/Sioux.html",
    "America/North/Yakima.html",
    "America/South-Central/Amazonian.html",
    "America/South-Central/Aztec.html",
    "America/South-Central/Inca.html",
    "America/South-Central/Maya.html",
    "America/South-Central/South.html",
    # India
    "India/Hindu-Gods/Deity-Groups.html",
    "India/Hindu-Gods/Demons.html",
    "India/Hindu-Gods/Goddesses.html",
    "India/Hindu-Gods/Gods.html",
    "India/Hindu-Gods/Hindu-Triad.html",
    "India/Hindu-Gods/Leaders.html",
    "India/Hindu-Gods/Minor-Gods.html",
    "India/Hindu-Gods/Planets.html",
    "India/Hindu-Gods/Vedic-Triad.html",
    "India/Hindu-Names/Emperors.html",
    "India/Hindu-Names/Nature.html",
    "India/Others/Buddhism.html",
    "India/Others/Jainism.html",
    "India/Others/Maldives.html",
    "India/Others/Sri-Lanka.html",
    "India/Sikh/Sikh.html",
    # Middle East
    "Middle-East/East/Afghanistan.html",
    "Middle-East/East/Bangladesh.html",
    "Middle-East/East/Iran.html",
    "Middle-East/East/Kurds.html",
    "Middle-East/East/Near-East.html",
    "Middle-East/East/Pakistan.html",
    "Middle-East/East/Turkey.html",
    "Middle-East/Jewish/Biblical.html",
    "Middle-East/Jewish/Modern.html",
    "Middle-East/Jewish/Various.html",
    "Middle-East/Jewish/Yiddish.html",
    # Orient
    "Orient/China/Manchu.html",
    "Orient/Himalayas/Bhutan.html",
    "Orient/Himalayas/Nepal.html",
    "Orient/Himalayas/Tibet.html",
    "Orient/Indochina/Burma.html",
    "Orient/Indochina/Cambodia.html",
    "Orient/Indochina/Laos.html",
    "Orient/Indochina/Thailand.html",
    "Orient/Indochina/Vietnam.html",
    "Orient/South-East-Asia/Brunei.html",
    "Orient/South-East-Asia/Indonesia.html",
    "Orient/South-East-Asia/Malaysia.html",
    "Orient/South-East-Asia/Philippines.html",
    # Pacific
    "Pacific/Melanesia/Papua-New-Guinea.html",
    "Pacific/Melanesia/Solomon-Islands.html",
    "Pacific/Melanesia/Tuvalu.html",
    "Pacific/Melanesia/Vanuatu.html",
    "Pacific/Micronesia/Belau.html",
    "Pacific/Micronesia/Guam.html",
    "Pacific/Micronesia/Kiribati.html",
    "Pacific/Micronesia/Marshall-Islands.html",
    "Pacific/Micronesia/Micronesia.html",
    "Pacific/Micronesia/Nauru.html",
    "Pacific/Polynesia/Aborigine.html",
    "Pacific/Polynesia/Cook-Islands.html",
    "Pacific/Polynesia/Easter-Island.html",
    "Pacific/Polynesia/Fiji.html",
    "Pacific/Polynesia/Hawaii.html",
    "Pacific/Polynesia/Maori.html",
    "Pacific/Polynesia/Samoa.html",
    "Pacific/Polynesia/Tahiti.html",
    "Pacific/Polynesia/Tonga.html",
]


# ---------------------------------------------------------------------------
# Common English words to filter out — these are never plausible as names
# ---------------------------------------------------------------------------

COMMON_WORDS = frozenset(
    {
        "abandoned",
        "able",
        "about",
        "above",
        "across",
        "actually",
        "added",
        "after",
        "again",
        "against",
        "aged",
        "ago",
        "agreed",
        "almost",
        "along",
        "already",
        "also",
        "although",
        "always",
        "among",
        "amongst",
        "another",
        "any",
        "anyone",
        "anything",
        "applied",
        "area",
        "around",
        "away",
        "back",
        "based",
        "became",
        "because",
        "become",
        "been",
        "before",
        "began",
        "behind",
        "being",
        "below",
        "beside",
        "besides",
        "best",
        "better",
        "between",
        "beyond",
        "big",
        "bit",
        "born",
        "both",
        "bottom",
        "brought",
        "built",
        "but",
        "called",
        "came",
        "can",
        "cannot",
        "carried",
        "case",
        "caused",
        "certain",
        "changed",
        "chief",
        "clear",
        "close",
        "combined",
        "come",
        "common",
        "commonly",
        "compound",
        "could",
        "coupled",
        "current",
        "cut",
        "dark",
        "day",
        "dead",
        "death",
        "derived",
        "did",
        "died",
        "different",
        "does",
        "done",
        "double",
        "down",
        "during",
        "each",
        "early",
        "either",
        "else",
        "end",
        "ending",
        "english",
        "enough",
        "especially",
        "etc",
        "even",
        "ever",
        "every",
        "everything",
        "example",
        "except",
        "extra",
        "fact",
        "far",
        "few",
        "finally",
        "find",
        "first",
        "five",
        "following",
        "for",
        "form",
        "formed",
        "former",
        "formerly",
        "found",
        "four",
        "free",
        "french",
        "full",
        "further",
        "gave",
        "general",
        "generally",
        "german",
        "get",
        "give",
        "given",
        "goes",
        "going",
        "gone",
        "good",
        "got",
        "great",
        "greek",
        "had",
        "half",
        "has",
        "have",
        "having",
        "held",
        "here",
        "herself",
        "high",
        "him",
        "himself",
        "his",
        "holy",
        "how",
        "however",
        "hundred",
        "into",
        "irish",
        "its",
        "just",
        "keep",
        "kept",
        "kind",
        "king",
        "known",
        "land",
        "large",
        "last",
        "late",
        "later",
        "latin",
        "least",
        "left",
        "less",
        "let",
        "like",
        "likely",
        "little",
        "local",
        "long",
        "look",
        "lord",
        "lost",
        "lot",
        "low",
        "made",
        "main",
        "make",
        "making",
        "man",
        "many",
        "may",
        "meaning",
        "means",
        "meant",
        "men",
        "might",
        "modern",
        "more",
        "most",
        "much",
        "must",
        "near",
        "nearly",
        "needed",
        "neither",
        "never",
        "new",
        "next",
        "nine",
        "noble",
        "none",
        "nor",
        "not",
        "nothing",
        "now",
        "number",
        "off",
        "often",
        "old",
        "older",
        "once",
        "one",
        "only",
        "open",
        "order",
        "other",
        "others",
        "our",
        "out",
        "over",
        "own",
        "part",
        "particularly",
        "passed",
        "perhaps",
        "place",
        "plus",
        "popular",
        "possible",
        "possibly",
        "probably",
        "put",
        "quite",
        "rather",
        "really",
        "red",
        "related",
        "remained",
        "rest",
        "right",
        "run",
        "said",
        "same",
        "saw",
        "second",
        "see",
        "seem",
        "seems",
        "seen",
        "sent",
        "set",
        "several",
        "she",
        "short",
        "should",
        "show",
        "shown",
        "similar",
        "simply",
        "since",
        "six",
        "small",
        "some",
        "something",
        "sometimes",
        "son",
        "soon",
        "sort",
        "spanish",
        "spoke",
        "still",
        "strong",
        "such",
        "sure",
        "take",
        "taken",
        "tell",
        "ten",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "therefore",
        "these",
        "they",
        "thing",
        "things",
        "think",
        "third",
        "this",
        "those",
        "though",
        "thought",
        "three",
        "through",
        "thus",
        "time",
        "together",
        "told",
        "too",
        "took",
        "top",
        "total",
        "towards",
        "turn",
        "turned",
        "two",
        "under",
        "unless",
        "until",
        "upon",
        "upper",
        "use",
        "used",
        "using",
        "usual",
        "usually",
        "various",
        "very",
        "want",
        "was",
        "way",
        "well",
        "went",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "white",
        "who",
        "whole",
        "whom",
        "whose",
        "why",
        "wide",
        "will",
        "with",
        "within",
        "without",
        "woman",
        "women",
        "word",
        "words",
        "work",
        "world",
        "would",
        "written",
        "year",
        "years",
        "yet",
        "you",
        "young",
        "your",
    }
)

# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------


class SectionAwareParser(HTMLParser):
    """Parse name pages tracking Male/Female/Surname section headings.

    Handles two page formats:
    - Table-based: names in <td> cells (first two columns: names + variants)
    - Plain-text: names as body text separated by commas/whitespace

    Section headings (h1-h6 containing "Male", "Female", etc.) switch the
    current category. Names outside any section are collected separately.
    """

    def __init__(self):
        super().__init__()
        self.male_names = set()
        self.female_names = set()
        self.surname_names = set()
        self.unsectioned_names = set()
        self._section = None
        self._in_heading = False
        self._in_td = False
        self._heading_text = []
        self._current_text = []
        self._td_index = 0
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = True
            self._heading_text = []
        elif tag == "td":
            self._in_td = True
            self._current_text = []
        elif tag == "tr":
            self._td_index = 0

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = False
            heading = "".join(self._heading_text).strip().lower()
            if "female" in heading or "women" in heading or "girl" in heading:
                self._section = "female"
            elif "male" in heading or "boy" in heading or heading == "men":
                self._section = "male"
            elif "surname" in heading:
                self._section = "surname"
            self._heading_text = []
        elif tag == "td":
            self._in_td = False
            text = "".join(self._current_text).strip()
            if self._td_index < 2 and text:
                self._add_names(text)
            self._td_index += 1
            self._current_text = []

    def handle_data(self, data):
        if self._in_heading:
            self._heading_text.append(data)
        elif self._in_td:
            self._current_text.append(data)
        else:
            if self._tag_stack and self._tag_stack[-1] in ("script", "style"):
                return
            stripped = data.strip()
            if stripped:
                self._add_names(stripped)

    def _add_names(self, text):
        names = clean_names(text)
        if self._section == "male":
            self.male_names.update(names)
        elif self._section == "female":
            self.female_names.update(names)
        elif self._section == "surname":
            self.surname_names.update(names)
        else:
            self.unsectioned_names.update(names)


# ---------------------------------------------------------------------------
# Name extraction and cleaning
# ---------------------------------------------------------------------------

# Alphabetic names, possibly with hyphens or apostrophes
_NAME_RE = re.compile(r"^[a-z][a-z'-]*[a-z]$|^[a-z]{2}$")

# Text patterns that are never names
_SKIP_RE = re.compile(
    r"(meaning|origin|variant|derivative|diminutive|history|"
    r"introduction|source|copyright|index|home|"
    r"see also|century|period|dynasty|"
    r"^the |^and |^or |^from |^of |^in |^to |^a |"
    r"^\d|http|www\.|\.html|\.htm)",
    re.IGNORECASE,
)


def clean_names(raw_text):
    """Extract individual names from a text chunk.

    Handles comma-separated lists, parenthetical notes, slash variants,
    and other formatting found on Onomastikon pages.
    """
    names = set()

    # Remove parenthetical and bracketed content
    text = re.sub(r"\([^)]*\)", " ", raw_text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = text.replace("?", "")

    # Split on commas, semicolons, slashes, newlines
    parts = re.split(r"[,;/\n]+", text)

    for part in parts:
        words = part.strip().split()
        for word in words:
            word = word.strip().strip(".-'\"").lower()
            word = re.sub(r"^[^a-z]+", "", word)
            word = re.sub(r"[^a-z]+$", "", word)
            if (
                len(word) >= 2
                and _NAME_RE.match(word)
                and not _SKIP_RE.search(word)
                and word not in COMMON_WORDS
            ):
                names.add(word)

    return names


# ---------------------------------------------------------------------------
# HTTP fetching
# ---------------------------------------------------------------------------


def fetch_page(url):
    """Fetch a URL and return its content as a string. Returns None on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AnagrammerNameScraper/1.0 (educational project)",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        print(f"  [WARN] Failed to fetch {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Page processing
# ---------------------------------------------------------------------------


def extract_all_names(html):
    """Parse a page and return names by section.

    Returns (male, female, surname, unsectioned) sets.
    """
    parser = SectionAwareParser()
    parser.feed(html)
    return (
        parser.male_names,
        parser.female_names,
        parser.surname_names,
        parser.unsectioned_names,
    )


def fetch_pages(page_list, page_type, male_set, female_set, surname_set):
    """Fetch a list of pages and add extracted names to the appropriate sets.

    page_type: "male", "female", "surname", or "mixed"
    """
    for path in page_list:
        url = BASE_URL + path
        time.sleep(REQUEST_DELAY)
        html = fetch_page(url)
        if not html:
            continue

        male, female, surname, unsectioned = extract_all_names(html)

        if page_type == "male":
            male_set.update(male | unsectioned)
        elif page_type == "female":
            female_set.update(female | unsectioned)
        elif page_type == "surname":
            surname_set.update(surname | unsectioned)
        elif page_type == "mixed":
            male_set.update(male)
            female_set.update(female)
            surname_set.update(surname)
            # Unsectioned names on mixed pages go to both genders
            male_set.update(unsectioned)
            female_set.update(unsectioned)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("Fetching names from Kate Monk's Onomastikon (tekeli.li)")
    print(f"  {len(MALE_PAGES)} male pages")
    print(f"  {len(FEMALE_PAGES)} female pages")
    print(f"  {len(SURNAME_PAGES)} surname pages")
    print(f"  {len(MIXED_PAGES)} mixed pages")
    total = len(MALE_PAGES) + len(FEMALE_PAGES) + len(SURNAME_PAGES) + len(MIXED_PAGES)
    print(f"  {total} pages total")
    print("=" * 60)

    all_male = set()
    all_female = set()
    all_surnames = set()

    print("\nFetching male pages...")
    fetch_pages(MALE_PAGES, "male", all_male, all_female, all_surnames)
    print(f"  {len(all_male):,} male names so far")

    print("\nFetching female pages...")
    fetch_pages(FEMALE_PAGES, "female", all_male, all_female, all_surnames)
    print(f"  {len(all_female):,} female names so far")

    print("\nFetching surname pages...")
    fetch_pages(SURNAME_PAGES, "surname", all_male, all_female, all_surnames)
    print(f"  {len(all_surnames):,} surnames so far")

    print("\nFetching mixed pages...")
    fetch_pages(MIXED_PAGES, "mixed", all_male, all_female, all_surnames)

    # Final filter: minimum length 2
    all_male = {n for n in all_male if len(n) >= 2}
    all_female = {n for n in all_female if len(n) >= 2}
    all_surnames = {n for n in all_surnames if len(n) >= 2}

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Male first names:   {len(all_male):,}")
    print(f"  Female first names: {len(all_female):,}")
    print(f"  Surnames:           {len(all_surnames):,}")

    # Write output files
    os.makedirs(DATA_DIR, exist_ok=True)

    for filename, names in [
        ("male_first.txt", all_male),
        ("female_first.txt", all_female),
        ("surnames.txt", all_surnames),
    ]:
        path = os.path.join(DATA_DIR, filename)
        sorted_names = sorted(names)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted_names) + "\n")
        print(f"  Wrote {len(sorted_names):,} names to {path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
