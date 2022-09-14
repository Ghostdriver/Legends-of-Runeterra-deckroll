metadata.json
{
	"locales": ["{string}", ...],
	"clientHash": "{string}"
	"gameplayDataHash": "{string}",
	"timestamp": "{YYYYMMDDhhmm}",
	"patchlineRef": "{string}"
}

cards.json
[
    {
        "id": "{cardCode}",
        "idComponents": 
        {
            "set": "setNumber",
            "region": 
            {
                "id": "{shortRegionCode}",
                "name": "{regionName}"
            }
        }
        "name": "{name}",
        "type": "{type}",
        "subType": "{subType}",
        "superType": "{superType}",
        "description": "{description}",
        "keywords": [],
        "associatedCards": [{cardCode}, ...]
        "health": "{health}",
        "attack": "{attack}",
        "cost": "{cost}",
        "assets":
        {
            "gameAbsolutePath": "http://{cdn}/{bundleName}/set1/en_us/img/card/game/{cardCode}.png"
        } 

    },
    {...}
]
