from neo4j import GraphDatabase
import json
import os

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "sifre??41"

driver = None
test_film = "The Matrix"

def test_baglanti():
    global driver
    try:
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        driver.verify_connectivity()
        print("Veritabanina baglandi. Test basarili")
        return True
    except:
        print("Veritabani baglanti testi basarisiz.")
        return False

def test_film_ara():
    query = """
    MATCH (m:Movie)
    WHERE toLower(m.title) CONTAINS toLower($kelime)
    RETURN m.title AS title
    LIMIT 1
    """
    with driver.session() as session:
        sonuc = session.run(query, kelime="matrix").single()

    if sonuc:
        print("Film arama fonksiyonu basarili")
        return True
    else:
        print("Film arama fonksiyonu basarisiz")
        return False

def test_film_detay():
    query = """
    MATCH (m:Movie {title:$title})
    RETURN m.title AS title, m.released AS year
    """
    with driver.session() as session:
        sonuc = session.run(query, title=test_film).single()

    if sonuc:
        print("Film detay goruntuleme basarili")
        return True
    else:
        print("Film detay goruntuleme basarisiz")
        return False

def test_json_olusturma():
    query = """
    MATCH (m:Movie {title:$title})
    OPTIONAL MATCH (m)<-[:ACTED_IN]-(p:Person)
    RETURN m.title AS film, collect(p.name) AS oyuncular
    """
    with driver.session() as session:
        sonuc = session.run(query, title=test_film).single()

    if not sonuc:
        print("json olusturulamadi")
        return False

    os.makedirs("exports", exist_ok=True)
    with open("exports/test_graph.json", "w", encoding="utf-8") as f:
        json.dump(dict(sonuc), f, ensure_ascii=False, indent=2)

    print("json dosyasi olusturuldu")
    return True

if __name__ == "__main__":
    print("test basladı")

    if test_baglanti():
        test_film_ara()
        test_film_detay()
        test_json_olusturma()

    print("test tamamlandi ")
