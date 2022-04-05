import re, requests
import pandas as pd
from bs4 import BeautifulSoup

def convertinoat(chaine:str):
    """
        Cette fonction convertit, si c'est possible, une chaîne chiffrée à la française (espace entre les milliers, virgules pour séparer des décimales) à un format anglo-saxon.
    """
    chaine=chaine.split(" (")[0]
    chaine=chaine.split("[")[0]
    chaine=chaine.replace("\n","")
    chaine=chaine.replace(u'\u200d', u'')
    chaine=chaine.replace(u'\xa0', u' ')
    reg_float=r"^[0-9]{1,3}( [0-9]{3})*,[0-9]+$"
    reg_int=r"^[0-9]{1,3}( [0-9]{3})*$"
    if re.match(reg_float,chaine):
        chaine=chaine.replace(" ","")
        chaine=chaine.replace(",",".")
    elif re.match(reg_int,chaine):
        chaine=chaine.replace(" ","")
    return chaine

def pivot_wiki(url:str,n_tableau:str,l_colonnes:list):
    """
        Cette fonction fait pivoter à la verticale des tableaux Wikipedia à une ligne et x colonnes pour la transformer en DataFrame de deux colonnes sur x lignes.
    """
    l_finale=[]
    l_DF=pd.read_html(url, match=n_tableau)
    DF=l_DF[0].copy()
    if len(l_DF)>1:
        for i in range(1,len(l_DF)):
            DF_trans=l_DF[i]
            for c in DF_trans.columns:
                DF[c]=DF_trans[c]
    for f_c in DF:
        l_finale.append({l_colonnes[0]:f_c,l_colonnes[1]:convertinoat(DF[f_c].iloc[0])})
    DF_finale=pd.DataFrame.from_dict(l_finale)
    return DF_finale

class Wikidaper:
    """
        Cette classe sert à aspirer les tableaux HTML qui contiennent des données classables dans une page Wikipedia.
        Les données chiffrées sont converties en entiers ou nombres à décimales et les tableaux restitués en DataFrames.
    """
    def __init__(self,url:str):
        """
            On initialise avec :
                - une URL renseignée par l'utilisateur, de préférence copiée/collée depuis le navigateur
                - un booléen de validation de cette dernière
                - une liste composée des tableaux classables trouvés sur la page
        """
        self.url=url
        self.valid_url=self.valide_url()
        if self.valid_url:
            self.l_tableaux=self.recolte_tableaux()
        else:
            self.l_tableaux=[]

    def valide_url(self):
        """
            Cette fonction va vérifier si l'URL rentrée par l'utilisateur renvoie vers une page Wikipedia susceptible d'avoir des tableaux avec données classables.
        """
        result=False
        regex="^http[s]{,1}:[/]{2}[a-z]{2,}\.wikipedia\.org/wiki/[A-Za-z0-9]+[_A-Za-z0-9]*"
        if re.match(regex, self.url):
            try:
                requests.get(self.url)
                result=True
            except:
                print("Cette page Wikipedia ne répond pas")
        else:
            print("Attention, votre URL ne pointe pas vers une page Wikipedia valide")
        return result

    def recolte_tableaux(self):
        """
            Cette fonction retourne une liste des tableaux classables trouvables sur une page Wikipedia.
            Elle reste vide s'il n'y a rien.
        """
        l_tableaux=[]
        url=requests.get(self.url)
        soupe=BeautifulSoup(url.text, "lxml")
        regex=re.compile('^wikitable.+sortable.*')
        for t in soupe.find_all("table", {"class" : regex}):
            l_tableaux.append(t)
        return l_tableaux

    def describe(self):
        """
            Cette fonction affiche les dimensions de chaque tableau de données classables trouvés dans la page Wikipedia renseignée
        """
        if self.l_tableaux==0:
            print("Il n'y a aucun tableau avec des données classables sur cette page Wikipedia")
        else:
            print(len(self.l_tableaux)," tableau(x) de données classables sur cette page, de dimension :")
            for t in self.l_tableaux:
                n_col=len([c.text for c in t.find_all("th") if not c.has_attr("colspan")])
                n_lignes=len([l for l in t.find_all("tr") if not l.findChildren("th" , recursive=False)])
                print(n_col," colonnes x",n_lignes,"lignes")

    def df_table(self,indice:int,l_except:list):
        """
            Cette fonction renvoie une DataFrame à partir d'un tableau listé dans l_tableaux.
        """
        indice=abs(indice)
        if len(self.l_tableaux)==0:
            print("Il n'y a aucun tableau avec des données classables sur cette page")
        elif indice>(len(self.l_tableaux)-1):
            print("Attention, vous devez interroger un indice compris entre 0 et ",(len(self.l_tableaux)-1))
        else:
            print("Transformation de la table ",indice,"en cours")
            l_dico=[]
            l_col=[c.text.split("[")[0].replace("\n","") for c in self.l_tableaux[indice].find_all("th") if not c.has_attr("colspan")]
            print("Colonnes trouvées :",l_col)
            for l in self.l_tableaux[indice].find_all("tr"):
                if not l.findChildren("th" , recursive=False):
                    if len(l.find_all("td"))==len(l_col):
                        l_dico.append({l_col[i]:convertinoat(l.find_all("td")[i].get_text()) for i in range(len(l_col))})
                    else:
                        l_rattrapage=[]
                        for e in l.find_all("td"):
                            if e.has_attr("colspan"):
                                doublon=convertinoat(e.get_text())
                                iterations=int(e.get("colspan"))
                                for i in range(iterations):
                                    l_rattrapage.append(doublon)
                            else:
                                l_rattrapage.append(convertinoat(e.get_text()))
                        l_dico.append({l_col[i]:l_rattrapage[i] for i in range(len(l_col))})
            DF=pd.DataFrame.from_dict(l_dico)
            for c in DF.columns:
                if c not in l_except:
                    try:
                        DF[c]=DF[c].astype(int)
                    except ValueError:
                        try:
                            DF[c]=DF[c].astype(float)
                        except ValueError:
                            pass
            return DF
