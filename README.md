# 2 Tablica usmjeravanja

## Instalacija


Kako bi paketi i moduli u ovom repozitoriju postali dostupni u pymote *virtual envinroment*-u potrebno je korijenski direktorij dodati u `sys.path`.
To je najlakše učiniti tako što će se u `site-packages` direktoriju unutar `pymote_env` direktorija (npr. `pymote_env\Lib\site-packages` u windows ili `pymote_env/lib/python2.7/site-packages` u linux OS-u) kreirati `pymote.pth` datoteka u kojoj treba u prvom retku zapisati punu putanju do korijenskog direktorija ovog repozitorija primjerice `/home/user/bmo/zadace/2-routing`.


## Zadatak

Implementirati algoritam za izračun tablice usmjeravanja (engl. *routing table*) najkraćim putovima za sve čvorove u mreži.


* Osmisliti i implementirati algoritam u modulu `pymote.algorithms.bmo2018.routing`.
    * Algoritam mora biti raspodijeljen, a čvorovi mogu koristiti samo informacije inicijalno dobivene informacije kao što su prvi susjedi i težine putova do prvih susjeda te informacije dobivene komunikacijom.
* Algoritam ispitati koristeći gotove testove u modulu `pymote.tests.algorithms.bmo2018.test_routing` naredbom:
         ```
         python -m unittest -v pymote.tests.algorithms.bmo2018.test_routing
         ```
    * Kako bi testovi ispravno radili čvor inicijator mora u svoju memoriju pod ključem `self.routingTableKey` zapisati tablicu usmjeravanja kao `dict` u kojem su ključevi svi čvorovi u mreži osim njega samoga, a za svaki čvor ključ vrijednost mora biti prvi susjed inicijatora na najkraćem putu između inicijatora i čvora ključa.
    Također svi čvorovi na kraju izvršavanja algoritma moraju završiti u statusu `'DONE'`, osim inicijatora koji završava u statusu `'INITIATOR'`.