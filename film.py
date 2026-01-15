from neo4j import GraphDatabase
import json
import os

URL = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "sifre??41"

class Renk:
    kirmizi = '\033[31m'
    yesil = '\033[92m'
    sari = '\033[93m'
    sade = '\033[0m'
    mavi = '\033[96m'
kopru = None
secili_film = None
def baglan():#veritabanına bağlanmamızı sağlıyor kopru aslında driver olarak kullaniliyor
    global kopru
    try:
        kopru = GraphDatabase.driver(URL, auth=(USERNAME, PASSWORD))
        kopru.verify_connectivity()
        return True
    except:
        print(f"{Renk.kirmizi}Neo4j'e baglanti basarisiz.{Renk.sade}")
        return False

def film_ara():#film aramamızı sağlıyor, kelimeyle eşleşen tüm filmleri sırayla listeliyor
    global secili_film

    aranacak = input(f"{Renk.sari}Aranacak film adı:{Renk.sade} ").strip()

    if aranacak == "":
        print(f"{Renk.kirmizi}Boş arama yapamazsın!{Renk.sade}")
        return

    query = """
    MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($kelime)
    RETURN m.title AS title, m.released AS year
    """
    with kopru.session() as session:
        sonuc = session.run(query, kelime=aranacak)
        filmler = list(sonuc)

    if len(filmler) == 0:
        print(f"{Renk.kirmizi}Sonuç yok.{Renk.sade}")
        return

    print(f"\n{Renk.yesil}Bulunan Filmler:{Renk.mavi}")
    for i, f in enumerate(filmler):
        print(f"{i+1}) {f['title']} ({f['year']})")

    while True:
        try:
            secim = int(input(f"{Renk.sari}Film seç (numara):{Renk.sade} "))
            if secim < 1 or secim > len(filmler):
                print("Hatalı Giriş")
            else:
                secili_film = filmler[secim-1]["title"]
                print("Film seçildi:", secili_film)
                break
        except:
            print(f"{Renk.kirmizi}Sayı girişi yapmalısınız.{Renk.sade}")

def film_detay():#cypher diliyle seçilen filmin oyuncularını yöneticilerini ve çıkış yılını veritabanından çekip yazdırmamızı sağlıyor
    if secili_film is None:
        print(f"{Renk.kirmizi}Önce film seçmelisiniz.{Renk.sade}")
        return

    query = """
    MATCH (m:Movie {title:$title})
    OPTIONAL MATCH (m)<-[:DIRECTED]-(d:Person)
    OPTIONAL MATCH (m)<-[:ACTED_IN]-(a:Person)
    RETURN m.title AS title, m.released AS year, m.tagline AS tagline,
           collect(DISTINCT d.name) AS directors,
           collect(DISTINCT a.name)[0..5] AS actors
    """

    with kopru.session() as session:
        sonuc = session.run(query, title=secili_film)
        film = sonuc.single()

    if film is None:
        print(f"{Renk.kirmizi}Film bulunamadı.{Renk.sade}")
        return

    print("\nFilm Detayı")
    print(f"{Renk.kirmizi}Ad:{Renk.sade}", film["title"])
    print(f"{Renk.kirmizi}Çıkış Yılı:{Renk.sade}", film["year"])

    if film["tagline"]:
        print(f"{Renk.kirmizi}Tagline(Slogan):{Renk.sade}", film["tagline"])

    print(f"{Renk.kirmizi}Yönetmen:{Renk.sade}")
    for y in film["directors"]:
        print("-", y)

    print(f"{Renk.kirmizi}Oyuncu Kadrosu:{Renk.sade}")
    for o in film["actors"]:
        print("-", o)

def graph_json():#graf fonksiyonu düğüm ve bağlantı oluşturuyor birbiriyle ilişkilerini gösteren json dosyası oluşturmamızı sağliyor
    if secili_film is None:
        print(f"{Renk.kirmizi}Önce film seçmelisiniz.{Renk.sade}")
        return

    query = """
    MATCH (m:Movie {title:$title})
    OPTIONAL MATCH (m)<-[r:ACTED_IN]-(a:Person)
    OPTIONAL MATCH (m)<-[r2:DIRECTED]-(d:Person)
    RETURN m, collect(DISTINCT a) AS actors, collect(DISTINCT d) AS directors
    """

    with kopru.session() as session:
        sonuc = session.run(query, title=secili_film).single()

    if not sonuc:
        print(f"{Renk.kirmizi}JSON oluşturulamadı.{Renk.sade}")
        return

    nodes = []
    links = []
    node_ids = {}
    def node_ekle(node, label):#düğüm oluşturuyor
        if node is None:
            return
        nid = node.element_id
        if nid not in node_ids:
            node_ids[nid] = len(nodes)
            nodes.append({
                "id": node_ids[nid],
                "label": label,
                "name": node.get("title") or node.get("name")
            })
        return node_ids[nid]
    m_node = sonuc["m"]
    film_id = node_ekle(m_node, "Movie")
    for oyuncu in sonuc["actors"]:
        oyuncu_id = node_ekle(oyuncu, "Person")
        links.append({
            "source": oyuncu_id,
            "target": film_id,
            "type": "oyuncu"
        })
    for yonetmen in sonuc["directors"]:
        yonetmen_id = node_ekle(yonetmen, "Person")
        links.append({
            "source": yonetmen_id,
            "target": film_id,
            "type": "yonetmen"
        })

    graph = {
        "nodes": nodes,
        "links": links
    }

    os.makedirs("exports", exist_ok=True)
    with open("exports/graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=1, ensure_ascii=False)

    print(f"{Renk.yesil}Graph dosyası oluşturuldu.{Renk.sade}")

def main():#main fonksiyonu kullanıcı arayüzünü ve seçim yapmamızı sağlayan kısmı gösteriyor
    print(f"{Renk.mavi}\n| Film Platformu |")
    print("1. Film Ara")
    print("2. Seçilen film için detay göster")
    print("3. Seçili film için graph json dosyası oluştur")
    print(f"4. Çıkış{Renk.sade}")

if not baglan():
    exit()
while True:
    main()
    secim = input(f"{Renk.sari}Seçim: ")

    if secim == "1":
        film_ara()
    elif secim == "2":
        film_detay()
    elif secim == "3":
        graph_json()
    elif secim == "4":
        print(f"{Renk.yesil}Çıkış yapıldı.{Renk.sade}")
        break
    else:
        print(f"{Renk.kirmizi}Yanlış seçim!{Renk.sade}")
