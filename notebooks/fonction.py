import numpy as np
import matplotlib.pyplot as plt
import xarray as xr

#-------------------------------------------------------------
#            P1: FONCTIONS ANALYSE DES PROXIES DE SURFACE
#-------------------------------------------------------------


def extraction_proxies():
    #Charge le fichier NetCDF et extrait les proxies de surface 


    chemin="../data/glorys_sst_sss_ssh_2015_2024.nc"
    ds=xr.open_dataset(chemin)

    sst = ds["thetao"].isel(depth=0).squeeze(drop=True)
    sss = ds["so"].isel(depth=0).squeeze(drop=True)
    ssh = ds["zos"]
    return sst, sss, ssh

def moyenne_saisonniere(var, season):
    #Calcule la moyenne saisonnière, la variable saison vaut "DJF" ou "JJA" 
    return var.where(var.time.dt.season == season, drop=True).mean("time")

def climatologie_mensuelle(variable):
    #Calcule une moyenne pour chaque mois de l'année sur la période 2015-2025
    return variable.groupby("time.month").mean("time")

def amplitude_saisonniere(variable):
    #Calcule l'amplitude saisonnière : maximum mensuel climatologique - minimum mensuel climatologique
    climatologie = climatologie_mensuelle(variable)
    return climatologie.max("month") - climatologie.min("month")


def anomalies_mensuelles(variable):
    #Calcule les anomalies mensuelles après retrait du cycle saisonnier moyen
    climatologie = climatologie_mensuelle(variable)
    return variable.groupby("time.month") - climatologie


def gradient(variable):
    #Calcule la norme du gradient en projetant les dérivées partielles sur la sphère terrestre
    
    R = 6371000  # rayon de la Terre en mètres
    lat_rad = np.deg2rad(variable.latitude)

    dvar_dy = variable.differentiate("latitude") / (R * np.pi / 180)
    dvar_dx = variable.differentiate("longitude") / (R * np.cos(lat_rad) * np.pi / 180)

    gradient = np.sqrt(dvar_dx**2 + dvar_dy**2)

    return gradient

def variabilite_residuelle(variable):
    #Calcule la variabilité résiduelle : écart-type des anomalies mensuelles
    anomalies = anomalies_mensuelles(variable)
    return anomalies.std("time")

#---------------Representation graphique

def echelle_commune(cartes):
    #Calcule une échelle de couleur commune à plusieurs cartes.
    vmin = min(float(carte.min()) for carte in cartes)
    vmax = max(float(carte.max()) for carte in cartes)
    return vmin, vmax

def carte(carte1, titre1, titre1_cbar,carte2=None, titre2=None, titre2_cbar=None,carte3=None, titre3=None, titre3_cbar=None,cmap=None, figsize=(14, 5), same_scale=False):
    # Trace 1, 2 ou 3 cartes côte à côte 
    cartes = [c for c in [carte1, carte2, carte3] if c is not None]
    titres = [t for c, t in zip([carte1, carte2, carte3],[titre1, titre2, titre3]) if c is not None]
    titres_cbar = [tc for c, tc in zip([carte1, carte2, carte3],[titre1_cbar, titre2_cbar, titre3_cbar]) if c is not None]

    fig, axes = plt.subplots(1, len(cartes), figsize=figsize)
    if len(cartes) == 1:
        axes = [axes]

    if same_scale:
        vmin, vmax = echelle_commune(cartes)

    for ax, carte, titre, titre_cbar in zip(axes, cartes, titres, titres_cbar):
        if not same_scale:
            vmin, vmax = carte.min(), carte.max()
        carte.plot(ax=ax,cmap=cmap,vmin=vmin,vmax=vmax,cbar_kwargs={"label": titre_cbar})
        ax.set_title(titre)

    plt.tight_layout()
    plt.show()
    
#-------------------------------------------------------------
#             P2 : FONCTION IMPACTE DE LA RESOLUTION SPATIALE
#-------------------------------------------------------------

def selection_gulf_stream(variable):
    #Sélectionne le domaine Gulf Stream.
    return variable.sel(latitude=slice(30, 50),longitude=slice(-80, -40))

def degradation_resolution(variable, facteur=3):
    #Dégradation spatiale en remplacant par la moyenne locale : pour GLORYS 1/12° un facteur=3 donne une pseudo-résolution 1/4°
    return variable.coarsen(latitude=facteur,longitude=facteur,boundary="trim").mean()

def gradient_p95(variable):
    #Calcule le quantile 95 du gradient spatial pour avoir les valeurs les plus fortes du gradient
    grad_t = gradient(variable)
    return grad_t.quantile(0.95, dim="time")
