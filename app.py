from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import requests
import folium
from bs4 import BeautifulSoup
import re
import pandas as pd
from wilayas import wilaya


app = Flask(__name__)

@app.route('/')
def my_form():
    return render_template('my-form.html')

@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    text = request.form['text']

    url = "https://www.emploitic.com/offres-d-emploi?q="
    url = url + text
    doc = BeautifulSoup(url, "lxml")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.0 Safari/537.36'}
    response = requests.get(url, headers=headers)
    result = BeautifulSoup(response.content, "lxml")
    cont = result.find_all('script')
    varr = str(cont[22])
    urls = re.findall('(?P<url>https://www.emploitic.com/offres-d-emploi/offre-d-emploi/algerie/[0-9a-z/-]+)', varr)#[a-zA-Z0-9-]

    location_job_list = []
    for i in urls:
        remover= i[65:]
        location_job_list.append(remover)
    job_title = []
    cleaned_list = [i.split('/') for i in location_job_list]
    for i in cleaned_list:
        if len(i)==3:
            del i[1]
        if len(i)==1:
            del i
    df = pd.DataFrame(cleaned_list)
    df[1] = df[1].str.replace(r'[\d+-]', ' ')
    df['Address'] = urls
    df.columns = ['location', 'job_title', "adress"]
    df.dropna(inplace=True)

    wil = pd.DataFrame(wilaya)
    wil1 = wil[["name", "latitude", "longitude"]]
    wil1.columns = ["location", "latitude", "longitude"]
    wil1["location"] = wil1["location"].str.lower()
    merg = pd.merge(df, wil1)
    merg["link"]='<li><a href=' +merg["adress"]+ '>'+merg["job_title"]+'</a></li>'
    final_df = merg.groupby(["location", "latitude", "longitude"])['link'].apply(lambda x: ''.join(x.astype(str))).reset_index()

    m = folium.Map(location=[36.7538259,3.057841], zoom_start=7)
    final_df.apply(lambda row:folium.Marker(location=[row["latitude"], row["longitude"]],
                                              radius=10, tooltip = str(len(re.findall("<li>", row["link"])))+" offer(s)", popup="<b>"+row["location"]+":"+"<b/>"+row["link"], icon=folium.Icon(color='red', icon='fa-map-pin', prefix='fa'))
                                             .add_to(m), axis=1)
    search_box = f'''
      <form method="POST">
        <input name="text">
        <input type="submit" value="Enter Job Title" />
      </form>
              <text>number of {text} jobs is {len(df)}</text>  

    '''
    return search_box + m._repr_html_()
if __name__ == "__main__":
            app.run(debug=True)
