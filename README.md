# Aplicatie disertație - Dezvoltarea unei aplicații mobile GIS

Funcții implementate:
  - încărcare basemap: OpenStreetMap sau Ortofoto;
  - Meniu lateral (stânga) care permite: crearea unei echipe, intrarea (join) la o echipă, panou afișare conectat/deconectat,
  - crearea de echipe / conectarea la o echipa deja creata pe server (serverul este creat cu FastAPI pe o VM cu Ubuntu OS),
  - Zoom in/out,
  - Măsurare distanțe/arii/perimetru,
  - Afișare/ascundere layere,
  - Ștergerea layerelor,
  - Selectare layere (elemente vectoriale: punct/linie/suprafață),
  - Clear (deselectarea elementelor selectate),
  - Modificarea proprietăților unui/unor elemente (se pot selecta mai multe elemente de clase diferite si schimba culoarea),
  - Meniu editare: creare punct/linie/suprafata + buton_start_editare + buton_stop_editare,
  - funcționalitate dinamica (start_edit activeaza creare_punct/lini/arie si butonul stop_edit, iar butonu stop_edit le dezactiveaza pe cele enumerate si il activeaza pe start_edit). Asemanator si in cazul delete-select_elements_clear,
  - Mesaje de informare (pop-up).
    
Ce urmeaza de implementat:
  - salvarea pe server a datelor vectoriale (deocamdata sunt salvate intr-o variabila locală din BasemapContainer: self.features). Variabila salveaza intr-o lista de dictionare: id_element, tipul_elementului, coordonatele (lat, lon), user_id, team_id, culoarea, descrierea. In cazul punctelor se salveaza si simbolul folosit,
  - accesarea serverului prin WAN, deocamdata merge doar in cadrul LAN,
  - afisarea pe harta a utilizatorilor,
  - functia de find_me care sa faca zoom pe locatia utilizatorului curent,
  - functia find_user_by_user_id, reprezentata prin MDIconButton cu icon=magnify (lupă) -- sunt cele cu culoarea rosie din imaginea 1.

## Screenshots

### 1. Prezentare Generală
Elementele trasate cu rosu nu au fost inca implementate.
![Prezentare Generală](img_git/1.png)

### 2. Selectare basemap
![Selectare basemap](<img_git/2 (selectare basemap).png>)

### 3. Basemap OSM selectat
![Selectare OSM](<img_git/3 (basemap_OSM).png>)

### 4. Meniu
![Meniu](<img_git/4 (meniu).png>)

### 5. Conectare la server
![Conectare la server](<img_git/5 (conectare la server).png>)

### 6. Mesaj confirmare conectare
![Confirmare](<img_git/6 (msj_confirmare_conn).png>)

### 7. Meniu actualizat
![Meniu actualizat](<img_git/7 (Meniu_actualizat).png>)

### 8. Calculare distanță (daca e mai mica de 1km este afisata in m, altfel in km)
![Distanța](<img_git/8(distanta).png>)

### 9. Calculare arie și perimetru
![Arie și perimetru](<img_git/9(arie+perimetru).png>)

### 10. Creare punct
![Creare punct](<img_git/10 (creare_pct).png>)

### 11. Selectare element
![Selectare element](<img_git/11 (selectare_elem).png>)

### 12. Modificare atribute / proprietati (culoarea in acest caz)
![Modificare atribute](<img_git/12 (modificare_prop [atribute]).png>)

### 13. Elemente șterse
![Elemente șterse](<img_git/13 (elem sterse).png>)

### 14. Mod editare
![Mod editare](<img_git/14 (mod_editare).png>)
