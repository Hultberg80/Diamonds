import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Sidkonfiguration
st.set_page_config(
    page_title="Vad avgör priset på en diamant?",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    with st.spinner("Laddar data.."):

        pd.set_option("styler.render.max_elements", 647004)
    
    df = pd.read_csv('cleaned_diamonds.csv')

    # Se till att kategoriska variabler är rätt datatyp och ordnade
    cut_order = ['Fair', 'Good', 'Very Good', 'Premium', 'Ideal']
    color_order = ['D', 'E', 'F', 'G', 'H', 'I', 'J']  # D = bäst, J = sämst
    clarity_order = ['IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2', 'I1']  # IF = bäst
    
    df['cut'] = pd.Categorical(df['cut'], categories=cut_order, ordered=True)
    df['color'] = pd.Categorical(df['color'], categories=color_order, ordered=True)
    df['clarity'] = pd.Categorical(df['clarity'], categories=clarity_order, ordered=True)
    
    # Beräkna volym
    df['volym'] = df['x'] * df['y'] * df['z']
    df['volume'] = df['volym']  # Alias för konsistens
    
    # Skapa ordinala versioner för analys så högre siffra = bättre kvalitet
    df['cut_ord'] = df['cut'].cat.codes + 1
    df['color_ord'] = df['color'].cat.codes + 1  # D=1, E=2, ..., J=7 - men D är bäst
    df['clarity_ord'] = df['clarity'].cat.codes + 1  # IF=1, VVS1=2, ..., I1=8 - men IF är bäst
    
    # Korrigera ordinala så högre värde = bättre kvalitet
    df['color_ord'] = len(color_order) + 1 - df['color_ord']  # Vänd så D=7, J=1
    df['clarity_ord'] = len(clarity_order) + 1 - df['clarity_ord']  # Vänd så IF=8, I1=1

    # Skapa karatgrupper
    # Automatisk uppdelning med pandas cut
    df['carat_group_auto'] = pd.cut(df['carat'], bins=5, labels=['Mycket liten', 'Liten', 'Medium', 'Stor', 'Mycket stor'])
    
    # Manuell uppdelning med ordnad kategorisk variabel
    def categorize_carat(carat):
        if carat < 0.5:
            return 'Liten (< 0.5)'
        elif carat < 1.0:
            return 'Medium (0.5-1.0)'
        elif carat < 1.5:
            return 'Stor (1.0-1.5)'
        elif carat < 2.0:
            return 'Mycket stor (1.5-2.0)'
        else:
            return 'Exceptionell (>2.0)'
    
    df['carat_group'] = df['carat'].apply(categorize_carat)
    
    # Gör karatgrupper till ordnad kategorisk variabel
    carat_group_order = ['Liten (< 0.5)', 'Medium (0.5-1.0)', 'Stor (1.0-1.5)', 'Mycket stor (1.5-2.0)', 'Exceptionell (>2.0)']
    df['carat_group'] = pd.Categorical(df['carat_group'], categories=carat_group_order, ordered=True)

    return df

df = load_data()

# sidebar
st.sidebar.header("Navigering")
page = st.sidebar.radio(
    "Välj sida:",
    ["Översikt", "Numeriska Egenskaper", "Kategoriska Egenskaper", "Samband & Korrelationer", "Karatgruppsanalys", "Slutsats"]
)

st.sidebar.header("Filtrera Data")

min_carat, max_carat = st.sidebar.slider(
    "Karat intervall:",
    min_value=int(df['carat'].min()),
    max_value=int(df['carat'].max()),
    value=(int(df['carat'].min()), int(df['carat'].max()))
)

min_volume, max_volume = st.sidebar.slider(
    "Volymintervall:",
    min_value=int(df['volume'].min()),
    max_value=int(df['volume'].max()),
    value=(int(df['volume'].min()), int(df['volume'].max()))
)

min_price, max_price = st.sidebar.slider(
    "Prisintervall:",
    min_value=int(df['price'].min()),
    max_value=int(df['price'].max()),
    value=(int(df['price'].min()), int(df['price'].max()))
)

selected_cuts = st.sidebar.multiselect(
   "Välj slipningar:",
    options=df['cut'].unique(),
    default=df['cut'].unique() 
)

# Filtrera data baserat på val
filtered_df = df[
    (df['cut'].isin(selected_cuts)) &
    (df['price'] >= min_price) &
    (df['price'] <= max_price) &
    (df['volume'] >= min_volume) &
    (df['volume'] <= max_volume) &
    (df['carat'] >= min_carat) &
    (df['carat'] <= max_carat)
]

# Funktion för att skapa en figur
def create_figure(figsize=(10, 6)):
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax

# ÖVERSIKT
if page == "Översikt":

    st.title("Vad avgör priset på en diamant?")
    st.info("""
    Vad är det som avgör priset på en diamant? I denna analys ska vi försöka ta reda på det.
    Och om du inte kan allt om diamanter,
    så kolla in fliken nedan för att få en bättre inblick.
    """)

    with st.expander("Förstå diamanternas värld - De Fyra C:na", expanded=False):
        st.markdown("""
        Diamantprissättning baseras på **"De Fyra C:na"** - fyra kritiska kvalitetsfaktorer som tillsammans bestämmer en diamants värde:
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🔸 **Carat (Karatvikt)**
            - Diamantens vikt, ursprungligen baserat på "carob seed" som var uniform i storlek
            - Större diamanter är exponentiellt dyrare (inte linjärt)
            
            ### ✂️ **Cut (Slipning)** 
            - Kvaliteten på diamantens slipning påverkar ljusreflektion
            - Skala: Fair → Good → Very Good → Premium → **Ideal** (bäst)
            - Ideal cut maximerar "brilliance" (ljusreflektion)
            """)
        
        with col2:
            st.markdown("""
            ### 🌈 **Color (Färg)**
            - Färgskala från **D (färglös, bäst)** till **J (synligt färgad)**
            - D, E, F = Färglösa (dyrast)
            - G, H, I = Nästan färglösa  
            - J = Synligt färgad (billigast i datasetet)
            
            ### 🔍 **Clarity (Klarhet)**
            - Mäter interna och externa defekter
            - **IF** (Internally Flawless) = Perfekt
            - **VVS1, VVS2** = Very Very Slightly Included
            - **VS1, VS2** = Very Slightly Included  
            - **SI1, SI2** = Slightly Included
            - **I1** = Included (defekter synliga för blotta ögat)
            """)
        
        st.markdown("""
        ---
        ### 📐 **Fysiska mått**
        - **x, y, z**: Längd, bredd, höjd i millimeter
        - **Depth**: Djupprocent = `2 × z/(x + y)` - optimalt runt 60-62%
        - **Table**: Bordets bredd relativt diamantens bredaste punkt - optimalt 53-58%
        - **Volym**: `x × y × z` - ger verklig storleksuppfattning""")

    st.header("Datasetsöversikt")
    st.info("""
    Vi går vidare genom att titta på analyser av diamanter baserat på olika egenskaper som karatvikt, slipning, färg och klarhet.
    Du kan utforska data genom att välja olika visualiseringar i sidofältet.
    """)
    
    # Visa rådata
    st.subheader("Rådata")
    st.dataframe(filtered_df.head(100), use_container_width=True)
    
    # Sammanfattande statistik
    st.subheader("Sammanfattande Statistik")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Antal diamanter", f"{len(filtered_df)}")
        st.metric("Genomsnittspris", f"${filtered_df['price'].mean():.2f}")
        st.metric("Genomsnittlig karatvikt", f"{filtered_df['carat'].mean():.2f}")
    
    with col2:
        st.metric("Vanligaste slipningen", f"{filtered_df['cut'].value_counts().idxmax() if not filtered_df.empty else 'N/A'}")
        st.metric("Vanligaste färgen", f"{filtered_df['color'].value_counts().idxmax() if not filtered_df.empty else 'N/A'}")
        st.metric("Prisintervall", f"${filtered_df['price'].min()} - ${filtered_df['price'].max()}")

    # Beskrivande statistik - ta bort price_predicted om den finns
    st.subheader("Beskrivande Statistik för Numeriska Egenskaper")
    desc_df = filtered_df.describe().T
    # Ta bort price_predicted om den finns
    if 'price_predicted' in desc_df.index:
        desc_df = desc_df.drop('price_predicted')
    st.dataframe(desc_df, use_container_width=True)

    # NUMERISKA EGENSKAPER
elif page == "Numeriska Egenskaper":
    st.header("Analys av Numeriska Egenskaper")
    
    st.info("""
    *"Hur ser fördelningen ut för olika egenskaper hos diamanter?"*

    Här undersöker vi egenskaper som karatvikt, pris och fysiska dimensioner. Genom att titta på histogram och boxplots kan vi upptäcka mönster som:

    - De flesta diamanter i datan är ganska små (under 1 karat)
    - Priset är ofta snedfördelat – det finns många billigare och några få extremt dyra
    - Några utliggare sticker ut – de kan vara exceptionellt stora eller unika diamanter

    Vi använder detta som grund för att förstå vad som är "normalt" i datamängden.
    """)
    
    # Välj variabel
    numeric_var = st.selectbox(
        "Välj numerisk variabel att analysera:",
        options=['carat', 'price', 'volym']
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Histogram över {numeric_var}")
        fig, ax = create_figure()
        sns.histplot(filtered_df[numeric_var], kde=True, ax=ax)
        ax.set_title(f'Fördelning av {numeric_var}')
        st.pyplot(fig)
    
    with col2:
        st.subheader(f"Boxplot för {numeric_var}")
        fig, ax = create_figure()
        sns.boxplot(y=filtered_df[numeric_var], ax=ax)
        ax.set_title(f'Boxplot av {numeric_var}')
        st.pyplot(fig)
    
    # Beskrivande statistik för den valda variabeln
    st.subheader(f"Statistik för {numeric_var}")
    stats = filtered_df[numeric_var].describe()
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Medelvärde", f"{stats['mean']:.2f}")
    with stat_col2:
        st.metric("Median", f"{stats['50%']:.2f}")
    with stat_col3:
        st.metric("Min", f"{stats['min']:.2f}")
    with stat_col4:
        st.metric("Max", f"{stats['max']:.2f}")
    
    # Lägg till insikter baserat på variabel
    if numeric_var == 'price':
        st.info("""
        **Insikter om pris:**
        - Prisfördelningen är ofta högersnedställd (många billiga, få dyra)
        - Outliers representerar exceptionellt dyra diamanter
        """)
    elif numeric_var == 'carat':
        st.info("""
        **Insikter om karatvikt:**
        - De flesta diamanter är relativt små (under 1 karat)
        - Stora diamanter (>2 karat) är mycket sällsynta
        """)
    elif numeric_var == 'volym':
        st.info("""
        **Insikter om volym:**
        - Volym korrelerar starkt med karatvikt
        - Extremvärden kan indikera onormala proportioner
        """)

      # KATEGORISKA EGENSKAPER
elif page == "Kategoriska Egenskaper":
    st.header("Analys av Kategoriska Egenskaper")
    
    st.info("""
    *"Spelar diamantens kvalitet någon roll för priset?"*

    Här fokuserar vi på de egenskaper som ofta kräver expertbedömning:

    - **Slipning (Cut):** hur väl diamanter reflekterar ljus
    - **Färg (Color):** färglösa diamanter är generellt mer eftertraktade
    - **Klarhet (Clarity):** hur många inre fel och ytfel diamanten har

    Här kan vi med hjälp av slidern till vänster, titta på fördelningen av diamanter i olika karatintervall till exempel.
    """)
    
    # Välj variabel
    cat_var = st.selectbox(
        "Välj kategorisk variabel att analysera:",
        options=['cut', 'color', 'clarity']
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Stapeldiagram för {cat_var}")
        fig, ax = create_figure()
        cat_counts = filtered_df[cat_var].value_counts().sort_index()
        sns.barplot(
        x=cat_counts.index,
        y=cat_counts.values,
        hue=cat_counts.index,           # Färg per kategori
        palette='plasma',               # Färgstark palett
        legend=False,
        ax=ax
        )
    
        ax.set_title(f'Antal diamanter per {cat_var}')
        ax.set_xlabel(cat_var.capitalize())
        ax.set_ylabel("Antal")
        ax.tick_params(axis='x', rotation=45)
        st.pyplot(fig)
    
    with col2:
        st.subheader(f"Fördelning av {cat_var}")
        # Skapa en tabell istället för cirkeldiagram
        cat_counts = filtered_df[cat_var].value_counts().sort_index()
        counts_df = pd.DataFrame({
            f'{cat_var.capitalize()}': cat_counts.index,
            'Antal': cat_counts.values,
            'Procent': (cat_counts.values / cat_counts.sum() * 100).round(1)
        })
        st.dataframe(counts_df, use_container_width=True, hide_index=True)
    
    # Genomsnittligt pris per kategori
    st.subheader(f"Genomsnittspris per {cat_var}")
    avg_price = filtered_df.groupby(cat_var)['price'].mean().sort_values(ascending=False)
    
    fig, ax = create_figure(figsize=(10, 5))
    sns.barplot(
    x=avg_price.index,
    y=avg_price.values,
    hue=avg_price.index,      # Färg per kategori
    palette='plasma',         # Färgpalett
    dodge=False,              # Viktigt för att inte separera staplarna
    legend=False,
    ax=ax
    )

    ax.set_title(f'Genomsnittspris per {cat_var}')
    ax.set_ylabel('Genomsnittspris (USD)')
    ax.set_xlabel(cat_var.capitalize())
    ax.tick_params(axis='x', rotation=45)

    st.pyplot(fig)
    
    # Lägg till insikter baserat på variabel
    if cat_var == 'cut':
        st.markdown("""
        **Insikter om slipning:**
        - "Ideal" och "Premium" cut har ofta högst pris
        - Slipningskvalitet påverker hur ljuset reflekteras
        - "Fair" cut är billigast men mindre attraktiv
        """)
    elif cat_var == 'color':
        st.markdown("""
        **Insikter om färg:**
        - D, E, F är färglösa och dyrast
        - G, H, I är nästan färglösa 
        - J är synligt färgad och billigast
        """)
    elif cat_var == 'clarity':
        st.markdown("""
        **Insikter om klarhet:**
        - IF (Internally Flawless) är perfekt och dyrast
        - VS1, VS2 har små defekter synliga under förstoring
        - SI1, SI2 har defekter synliga för tränat öga
        """)

elif page == "Samband & Korrelationer":
    st.header("Samband och Korrelationer")

    st.info("""
    I spridningsdiagrammet kan vi lite bättre se (även om det är plottrigt)
    hur kvaliteten (color, cut, clarity) minskar desto större diamanten är. Vi kan även se att "depth" och "table"
    inte har någon korrelation alls med priset, medan volymen har en stark korrelation, vilket
    vi även kan se i korrelationsmatrisen.
    """)

    # Spridningsdiagram
    st.subheader("Spridningsdiagram")
    x_var = st.selectbox("Välj X-variabel:", options=['carat', 'depth', 'table', 'x', 'y', 'z', 'volym'])
    y_var = st.selectbox("Välj Y-variabel:", options=['price', 'carat', 'depth', 'table', 'x', 'y', 'z', 'volym'], index=0)
    hue_var = st.selectbox("Välj gruppering (färg):", options=[None, 'cut', 'color', 'clarity'])

    fig, ax = create_figure()
    if hue_var:
        sns.scatterplot(x=x_var, y=y_var, hue=hue_var, data=filtered_df, ax=ax)
    else:
        sns.scatterplot(x=x_var, y=y_var, data=filtered_df, ax=ax)

    ax.set_title(f'Samband mellan {x_var} och {y_var}')
    st.pyplot(fig)

    # Visa sparad korrelationsmatris som bild
    st.subheader("Korrelationsmatris")
    st.markdown("Här ser du sambanden mellan numeriska egenskaper. Från mörkblå (svag korrelation) till mörkröd (stark korrelation).")
    st.image("korrelationsmatris.png", caption="Korrelationsmatris för numeriska variabler", use_container_width=True)

    # Korrelationstoppar
    st.subheader("Starkaste korrelationer")
    numeric_df = filtered_df.select_dtypes(include=[np.number])
    corr_matrix = numeric_df.corr()
    corr_unstack = corr_matrix.unstack()
    corr_unstack = corr_unstack[corr_unstack < 1.0]  # Ta bort självkorrelationer
    strongest_corr = corr_unstack.abs().sort_values(ascending=False).head(5)

    for i, (pair, corr_value) in enumerate(strongest_corr.items()):
        var1, var2 = pair
        st.write(f"{i+1}. {var1} - {var2}: {corr_value:.3f}")


    # KARATGRUPPSANALYS
elif page == "Karatgruppsanalys":
    st.header("Karatgruppsanalys")

    st.info("""
    *"Är större diamanter alltid bättre?"*

    Vi delar upp diamanterna i olika viktklasser och upptäcker ett intressant mönster:

    - **Ju större diamant, desto högre pris** – men...
    - **Kvaliteten (cut, clarity, color) sjunker ofta när vikten ökar**

    Det tyder på att större diamanter ofta görs av lägre kvalitet råmaterial – vilket kan bero på att det är svårare att hitta stora bitar med perfekt klarhet.

    Det finns alltså en avvägning: vill du ha storlek eller hög kvalitet?
    """)
    
    # Automatisk karatgruppsindelning
    st.subheader("Automatisk karatgruppsindelning")
    carat_counts_auto = filtered_df['carat_group_auto'].value_counts().sort_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Antal diamanter per karatgrupp (automatisk uppdelning)")
        fig_auto, ax_auto = create_figure()
        sns.barplot(x=carat_counts_auto.index.astype(str), y=carat_counts_auto.values, ax=ax_auto)
        ax_auto.set_xlabel("Karatgrupp")
        ax_auto.set_ylabel("Antal diamanter")
        ax_auto.set_title("Automatisk karatgruppsfördelning")
        ax_auto.tick_params(axis='x', rotation=45)
        st.pyplot(fig_auto)
    
    with col2:
        st.write("Fördelning av karatgrupper")
        # Skapa en enklare tabell istället för cirkeldiagram
        counts_df = pd.DataFrame({
            'Karatgrupp': carat_counts_auto.index,
            'Antal': carat_counts_auto.values,
            'Procent': (carat_counts_auto.values / carat_counts_auto.sum() * 100).round(1)
        })
        st.dataframe(counts_df, use_container_width=True, hide_index=True)
    
    # Manuell karatgruppsindelning
    st.subheader("Manuell karatgruppsindelning")
    
    # Skapa gruppsummering med rätt ordning
    group_summary = filtered_df.groupby('carat_group', observed=False).agg({
        'price': ['mean', 'median', 'count'],
        'volume': 'mean',
        'clarity_ord': 'mean',
        'cut_ord': 'mean',
        'color_ord': 'mean'
    }).round(2)
    
    # Platta till kolumnnamnen
    group_summary.columns = ['mean_price', 'median_price', 'count', 'mean_volume', 'mean_clarity_ord', 'mean_cut_ord', 'mean_color_ord']
    group_summary = group_summary.reset_index()
    
    # Sortera enligt vår önskade ordning
    carat_order = ['Liten (< 0.5)', 'Medium (0.5-1.0)', 'Stor (1.0-1.5)', 'Mycket stor (1.5-2.0)', 'Exceptionell (>2.0)']
    group_summary['carat_group'] = pd.Categorical(group_summary['carat_group'], categories=carat_order, ordered=True)
    group_summary = group_summary.sort_values('carat_group')
    
    st.write("Sammanfattning för manuellt definierade karatgrupper")
    st.dataframe(group_summary, use_container_width=True)
    
    # Visualiseringar för manuella grupper
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Snittpris per karatgrupp")
        fig_price, ax_price = create_figure()
        sns.barplot(data=group_summary, x='carat_group', y='mean_price', ax=ax_price)
        ax_price.set_ylabel("Genomsnittspris (USD)")
        ax_price.set_xlabel("Karatgrupp")
        ax_price.set_title("Genomsnittligt pris per karatgrupp")
        ax_price.tick_params(axis='x', rotation=45)
        st.pyplot(fig_price)
    
    with col2:
        st.write("Antal diamanter per manuell karatgrupp")
        fig_count, ax_count = create_figure()
        sns.barplot(data=group_summary, x='carat_group', y='count', ax=ax_count)
        ax_count.set_ylabel("Antal diamanter")
        ax_count.set_xlabel("Karatgrupp")
        ax_count.set_title("Antal diamanter per karatgrupp")
        ax_count.tick_params(axis='x', rotation=45)
        st.pyplot(fig_count)
    
    # Detaljerad analys per karatgrupp
    st.subheader("Detaljerad analys per karatgrupp")
    
    # Välj karatgrupp för djupare analys
    selected_carat_group = st.selectbox(
        "Välj karatgrupp för detaljerad analys:",
        options=filtered_df['carat_group'].unique()
    )
    
    group_data = filtered_df[filtered_df['carat_group'] == selected_carat_group]
    
    if not group_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Antal diamanter", len(group_data))
            st.metric("Genomsnittspris", f"${group_data['price'].mean():.2f}")
        
        with col2:
            st.metric("Medianpris", f"${group_data['price'].median():.2f}")
            st.metric("Genomsnittlig volym", f"{group_data['volume'].mean():.2f} mm³")
        
        with col3:
            st.metric("Vanligaste slipning", group_data['cut'].mode().iloc[0] if not group_data['cut'].mode().empty else 'N/A')
            st.metric("Vanligaste färg", group_data['color'].mode().iloc[0] if not group_data['color'].mode().empty else 'N/A')
        
        # Histogram för vald grupp
        st.write(f"Prisfördelning för {selected_carat_group}")
        fig_hist, ax_hist = create_figure()
        sns.histplot(group_data['price'], kde=True, ax=ax_hist)
        ax_hist.set_title(f'Prisfördelning för {selected_carat_group}')
        ax_hist.set_xlabel('Pris (USD)')
        st.pyplot(fig_hist)
    

    # Viktigt mönster - lägg till insikt
    st.info("""
    
    **Liten diamant → lågt pris, låg volym, hög klarhet/slipning/färg**
    
    **Större diamant → högre pris, högre volym, men lägre klarhet/slipning/färg**
    
    Detta visar att mindre diamanter ofta har högre kvalitet per karat, medan större diamanter är dyrare men har lägre genomsnittlig kvalitet.
    """)
    
    # Visa mönstret i form av trendanalys
    st.subheader("Trendanalys: Storlek vs Kvalitet")
    
    # Skapa trendvisualisering
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Pris & Volym trend (ökar med storlek)**")
        fig_trend1, ax_trend1 = create_figure()
        ax_trend1.plot(range(len(group_summary)), group_summary['mean_price'], 'o-', label='Genomsnittspris', color='green', linewidth=2)
        ax_trend1.set_xlabel('Karatgrupp (Liten → Stor)')
        ax_trend1.set_ylabel('Pris (USD)', color='green')
        ax_trend1.tick_params(axis='y', labelcolor='green')
        ax_trend1.set_xticks(range(len(group_summary)))
        ax_trend1.set_xticklabels([g.split(' ')[0] for g in group_summary['carat_group']], rotation=45)
        
        # Lägg till volym på sekundär y-axel
        ax2 = ax_trend1.twinx()
        ax2.plot(range(len(group_summary)), group_summary['mean_volume'], 's-', label='Volym', color='blue', linewidth=2)
        ax2.set_ylabel('Volym (mm³)', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')
        
        ax_trend1.set_title('Pris & Volym ökar med storlek')
        st.pyplot(fig_trend1)
    
    with col2:
        st.write("**Kvalitet trend (minskar med storlek)**")
        fig_trend2, ax_trend2 = create_figure()
        ax_trend2.plot(range(len(group_summary)), group_summary['mean_clarity_ord'], 'o-', label='Klarhet', linewidth=2)
        ax_trend2.plot(range(len(group_summary)), group_summary['mean_cut_ord'], 's-', label='Slipning', linewidth=2)
        ax_trend2.plot(range(len(group_summary)), group_summary['mean_color_ord'], '^-', label='Färg', linewidth=2)
        ax_trend2.set_xlabel('Karatgrupp (Liten → Stor)')
        ax_trend2.set_ylabel('Kvalitetspoäng (högre = bättre)')
        ax_trend2.set_xticks(range(len(group_summary)))
        ax_trend2.set_xticklabels([g.split(' ')[0] for g in group_summary['carat_group']], rotation=45)
        ax_trend2.legend()
        ax_trend2.set_title('Kvalitet minskar med storlek')
        st.pyplot(fig_trend2)
    
    # Detaljerade rapporter för varje grupp
    st.subheader("Detaljerade rapporter per karatgrupp")
    
    for group in group_summary['carat_group']:
        sub = filtered_df[filtered_df['carat_group'] == group]
        if sub.empty:
            continue

        with st.expander(f"🔹 Grupp: {group}"):
            st.write(f"**Antal diamanter:** {len(sub)}")
            st.write(f"**Genomsnittspris:** ${sub['price'].mean():.2f}")
            st.write(f"**Medianpris:** ${sub['price'].median():.2f}")
            st.write(f"**Genomsnittlig volym:** {sub['volume'].mean():.2f} mm³")
            st.write(f"**Genomsnittlig klarhet (ordinal):** {sub['clarity_ord'].mean():.2f}")
            st.write(f"**Genomsnittlig slipning (ordinal):** {sub['cut_ord'].mean():.2f}")
            st.write(f"**Vanligaste slipning:** {sub['cut'].mode().iloc[0] if not sub['cut'].mode().empty else 'N/A'}")
            st.write(f"**Genomsnittlig färg (ordinal):** {sub['color_ord'].mean():.2f}")
            st.write(f"**Vanligaste färg:** {sub['color'].mode().iloc[0] if not sub['color'].mode().empty else 'N/A'}")


else:
    st.header("Slutsats")

    st.info("""
    *"Vad har vi lärt oss?"*

Efter att ha analyserat tusentals diamanter ser vi tydligt att:

- **Karatvikt är den starkaste prispåverkande faktorn**
- **Färg, klarhet och slipning påverkar priset – men i mindre grad**
- **Större diamanter tenderar att ha lägre genomsnittlig kvalitet**
""")