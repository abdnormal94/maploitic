from flask import Flask, request, render_template
from bs4 import BeautifulSoup
import requests
import folium
from bs4 import BeautifulSoup
import re
import pandas as pd
from wilayas import wilaya
from flask import redirect, url_for


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def my_form_post():
    if request.method == 'POST':
        text = request.form['text']
        return redirect(url_for('search_results', keyword=text))
    return render_template('my-form.html')

@app.route('/search_results/<keyword>', methods=['GET', 'POST'])
def search_results(keyword):
    if request.method == 'POST':
        new_keyword = request.form['new_keyword']
        return redirect(url_for('search_results', keyword=new_keyword))
    #keyword = request.form['text']

    url = "https://www.emploitic.com/offres-d-emploi?q="
    url = url + keyword
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
    <script>
    document.title = "{keyword} - MAPLOITIC";
  </script>
    <style>
        .job-count {{
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-top: 20px;
        }}

        form {{
        margin-top: 20px;
        }}

        input[type="text"] {{
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
        outline: none;
        width: 300px;
        }}

        input[type="submit"] {{
        padding: 10px 20px;
        background-color: #4285f4;
        color: #fff;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
        }}

        input[type="submit"]:hover {{
        background-color: #357ae8;
        }}
    </style>

    <div style="background-color: #f3f6ee; padding: 20px;">
        <div style="display: flex; align-items: center;">
        <a href="/">
            <img src="/static/logo.png" alt="Logo" style="width: 100px; height: auto;">
        </a>
        <form method="POST">
            <input name="new_keyword" placeholder="Enter New Keyword">
            <input type="submit" value="Search">
        </form>
        </div>

        <p class="job-count">Number of job listings for "{keyword}": <span style="color: #4285f4;">{len(df)}</span></p>  

        <div style="margin-top: 20px;">
        {m._repr_html_()}
        </div>
    </div>
    '''
    return search_box 




if __name__ == "__main__":
            app.run(debug=True)


