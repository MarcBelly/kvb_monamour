from kvb_data import kvb_table_ma100, kvb_coefficients_ma100, kvb_table_me100, kvb_coefficients_me100, kvb_table_me120, kvb_coefficients_me120

def calculer_kvb_ma100(masse_totale, masse_freinee, type_train="MA100"):
    if type_train == "MA100":
        for (mt_min, mt_max, freins) in kvb_table_ma100:
            if mt_min <= masse_totale <= mt_max:
                for i, seuil in enumerate(freins):
                    if masse_freinee < seuil:
                        if i == 0:
                            return "Masse freinée insuffisante pour ce gros train!"
                        return kvb_coefficients_ma100[i-1]
                return kvb_coefficients_ma100[-1]
    return "Erreur : Masse totale hors plage couverte."

def calculer_kvb_me100(masse_totale, masse_freinee, type_train="ME100"):
    if type_train == "ME100":
        for (mt_min, mt_max, freins) in kvb_table_me100:
            if mt_min <= masse_totale <= mt_max:
                for i, seuil in enumerate(freins):
                    if masse_freinee < seuil:
                        if i == 0:
                            return "Masse freinée insuffisante pour ce gros train!"
                        return kvb_coefficients_me100[i-1]
                return kvb_coefficients_me100[-1]
    return "Erreur : Masse totale hors plage couverte."

def calculer_kvb_me120(masse_totale, masse_freinee, type_train="ME120"):
    if type_train == "ME120":
        for (mt_min, mt_max, freins) in kvb_table_me120:
            if mt_min <= masse_totale <= mt_max:
                for i, seuil in enumerate(freins):
                    if masse_freinee < seuil:
                        if i == 0:
                            return "Masse freinée insuffisante pour ce gros train!"
                        return kvb_coefficients_me120[i-1]
                return kvb_coefficients_me120[-1]
    return "Erreur : Masse totale hors plage couverte."