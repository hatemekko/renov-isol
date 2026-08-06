"""
Page : À propos — contexte du projet et limites.
"""
import streamlit as st

st.title("ℹ️ À propos")
st.markdown("---")

st.markdown("""
## RENOV'ISOL
### Outil d'aide à la décision pour l'isolation thermique par l'intérieur des bâtiments anciens

---

**Développé dans le cadre d'un projet de fin d'études du :**

> **Mastère Spécialisé Expert en Construction et Habitat Durables (ECHD)**
> Arts et Métiers, promotion 2025-2026

---

### Objectif

RENOV'ISOL permet de comparer des solutions d'isolation thermique par l'intérieur (ITI) 
dans des bâtiments anciens dont la façade ne peut pas être isolée par l'extérieur.

À performance thermique imposée, l'épaisseur posée dépend de la conductivité du matériau. 
L'outil quantifie la surface habitable consommée et calcule le coût global indicatif 
de chaque solution, en intégrant la valorisation économique de cette surface.

---

### Contexte

Dans les villes denses (Paris et autres marchés à prix élevé), la surface habitable perdue 
lors de l'isolation intérieure a une valeur de marché significative. 
Une solution plus chère à l'investissement peut se révéler plus avantageuse 
si elle préserve davantage de surface habitable.

L'outil permet de rendre cette comparaison explicite et transparente.

---

### Limites

Cet outil constitue une aide à la décision. Il **ne remplace pas** :
- une étude thermique réglementaire (DPE, calcul 3CL) ;
- une simulation thermique dynamique ;
- une étude hygrothermique détaillée (méthode Glaser, WUFI…) ;
- une expertise du bâtiment ;
- une étude économique complète (analyse de cycle de vie, financement…).

La valorisation économique de la surface consommée est un **coût d'opportunité indicatif**.
Elle dépend du prix de marché local, qui peut varier.

L'outil ne gère pas les ponts thermiques, les propriétés acoustiques, 
l'empreinte carbone des matériaux ni la durée de vie comparative des solutions.

---

### Données

Les données techniques et économiques des matériaux sont renseignées par l'administrateur 
à partir de sources documentées (fiches techniques, certifications ACERMI, FDES). 
L'application n'invente aucune donnée.

---

### Année
2025-2026
""")
