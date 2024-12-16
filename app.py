import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for non-interactive plotting

import logging
from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from flask import session
import pandas as pd
from werkzeug.utils import secure_filename
import os
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import skfuzzy as fuzz
import numpy as np
import matplotlib.patches as mpatches
from fpdf import FPDF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Fungsi untuk menjalankan K-Means
def run_kmeans(data, clusters):
    logging.debug('Menjalankan K-Means clustering')
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data.values)
    kmeans = KMeans(n_clusters=clusters, random_state=42, n_init=500)
    data['Cluster'] = kmeans.fit_predict(scaled_data)
    logging.debug(f'Hasil clustering K-Means: {data["Cluster"].value_counts()}')
    return data

# Fungsi untuk menjalankan Fuzzy C-Means
def run_fuzzy_cmeans(data, clusters):
    logging.debug('Menjalankan Fuzzy C-Means clustering')
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data.values)
    cntr, u, _, _, _, _, _ = fuzz.cluster.cmeans(scaled_data.T, clusters, 1.5, error=0.001, maxiter=5000, init=None)
    cluster_membership = np.argmax(u, axis=0)
    data['Cluster'] = cluster_membership
    logging.debug(f'Hasil clustering Fuzzy C-Means: {data["Cluster"].value_counts()}')
    return data

def interpret_clusters(cluster_means):
    interpretations = {}
    sorted_clusters = cluster_means.mean(axis=1).sort_values().index.tolist()
    size = len(sorted_clusters)

    # Tetapkan label berdasarkan jumlah cluster
    if size == 2:
        labels = ["Rendah", "Tinggi"]
    elif size == 3:
        labels = ["Rendah", "Sedang", "Tinggi"]
    elif size == 4:
        labels = ["Rendah", "Sedang", "Tinggi", "Sangat tinggi"]
    elif size == 5:
        labels = ["Rendah", "Sedang", "Di atas rata-rata", "Tinggi", "Sangat tinggi"]
    elif size == 6:
        labels = ["Sangat rendah", "Rendah", "Sedang", "Cukup tinggi", "Tinggi", "Sangat tinggi"]
    elif size == 7:
        labels = ["Sangat rendah", "Rendah", "Cukup rendah", "Sedang", "Cukup tinggi", "Tinggi", "Sangat tinggi"]
    elif size == 8:
        labels = ["Sangat rendah", "Rendah", "Cukup rendah", "Sedang", "Di atas rata-rata", "Cukup tinggi", "Tinggi", "Sangat tinggi"]
    elif size == 9:
        labels = ["Sangat rendah", "Rendah", "Cukup rendah", "Sedikit di bawah rata-rata", "Sedang", "Di atas rata-rata", "Cukup tinggi", "Tinggi", "Sangat tinggi"]
    elif size == 10:
        labels = ["Sangat rendah", "Rendah", "Cukup rendah", "Sedikit di bawah rata-rata", "Sedang", "Di atas rata-rata", "Cukup tinggi", "Tinggi", "Sangat tinggi", "Sangat rendah sekali"]
    elif size == 11:
        labels = ["Terendah", "Sangat rendah sekali", "Sangat rendah", "Rendah", "Cukup rendah", "Sedikit di bawah rata-rata", "Sedang", "Di atas rata-rata", "Cukup tinggi", "Tinggi", "Sangat tinggi"]

    # Tetapkan warna sesuai dengan label
    predefined_colors = {
        "Tinggi": "blue",
        "Sedang": "orange",
        "Rendah": "red"
    }
    extra_colors = ['gray', 'olive', 'cyan', 'purple', 'pink', 'brown', 'black', 'green', 'violet', 'yellow']
    colors = []

    for label in labels:
        if label in predefined_colors:
            colors.append(predefined_colors[label])
        else:
            colors.append(extra_colors.pop(0))

    for i, cluster in enumerate(sorted_clusters):
        interpretations[cluster] = labels[i]

    return interpretations, sorted_clusters, colors

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/riceplant101')
def riceplant101():
    return render_template('riceplant101.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/uploads/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/run-clustering', methods=['GET', 'POST'])
def run_clustering():
    if request.method == 'POST':
        if 'dataset' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['dataset']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and not file.filename.endswith('.xlsx'):
            flash('Maaf, pastikan format file adalah file excel (.xlsx)')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                logging.debug('Membaca file dataset')
                data = pd.read_excel(filepath, index_col='Lokasi')
                clusters = int(request.form['clusters'])
                algorithm = request.form['algorithm']
                logging.debug(f'Jumlah cluster yang dipilih: {clusters}')
                logging.debug(f'Algoritma yang dipilih: {algorithm}')
                
                # Simpan clusters dan algorithm ke session
                session['clusters'] = clusters
                session['algorithm'] = algorithm

                # Tentukan skala data
                is_kabupaten = any(data.index.str.contains('Kabupaten|Kota', case=False))
                if is_kabupaten:
                    logging.debug('Menggunakan shapefile level 2 (Kabupaten/Kota)')
                    shapefile_path = "gadm41_IDN_2.shp"
                    merge_on = "NAME_2"
                else:
                    logging.debug('Menggunakan shapefile level 1 (Provinsi)')
                    shapefile_path = "gadm41_IDN_1.shp"
                    merge_on = "NAME_1"

                # Jalankan algoritma yang dipilih
                if algorithm == 'kmeans':
                    logging.debug('Menjalankan model K-Means')
                    result = run_kmeans(data, clusters)
                    keterangan = f"Hasil Clustering Menggunakan Algoritma K-Means Clustering dengan {clusters} Cluster:"
                elif algorithm == 'fuzzy':
                    logging.debug('Menjalankan model Fuzzy C-Means')
                    result = run_fuzzy_cmeans(data, clusters)
                    keterangan = f"Hasil Clustering Menggunakan Algoritma Fuzzy C-Means dengan {clusters} Cluster:"

                # Buat interpretasi dan mapping warna
                cluster_means = result.groupby('Cluster').mean()
                interpretations, sorted_clusters, colors = interpret_clusters(cluster_means)

                color_map = {sorted_clusters[i]: colors[i] for i in range(len(sorted_clusters))}
                cluster_labels = {sorted_clusters[i]: f'Cluster {sorted_clusters[i]}' for i in range(len(sorted_clusters))}
                legend_patches = [mpatches.Patch(color=colors[i], label=f'Cluster {sorted_clusters[i]}') for i in range(len(sorted_clusters))]

                # Buat visualisasi distribusi cluster
                try:
                    logging.debug('Membuat visualisasi distribusi cluster')
                    cluster_distribution = result['Cluster'].value_counts().reindex(sorted_clusters)
                    logging.debug(f'Distribusi cluster: {cluster_distribution}')

                    color_map = {sorted_clusters[i]: colors[i] for i in range(len(sorted_clusters))}

                    ax = cluster_distribution.plot(kind='bar', color=[color_map[c] for c in sorted_clusters])
                    plt.title('Plot Distribusi Cluster')
                    plt.xlabel('Cluster')
                    plt.ylabel('Jumlah Lokasi')
                    plt.grid(True)

                    # Tambahkan anotasi jumlah anggota cluster di bagian bawah grafik
                    annotation_text = "\n".join([f"Cluster {c} = {cluster_distribution[c]}" for c in sorted_clusters])
                    plt.annotate(annotation_text, xy=(0.87, 0.95), xycoords='axes fraction', fontsize=10, ha='center', va='top', bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))
                    plt.savefig('static/distribution.png')
                    plt.close()
                except Exception as e:
                    logging.error('Error: %s', e)
                    flash('An error occurred while creating the visualization.')

                # Buat visualisasi peta
                try:
                    logging.debug('Mulai membuat peta...')
                    kamus_penyesuaian = {
                        "Daerah Khusus Ibukota Jakarta": "Jakarta Raya",
                        "Kepulauan Bangka Belitung": "Bangka Belitung",
                        "Daerah Istimewa Yogyakarta": "Yogyakarta",
                    }

                    logging.debug(f'Muat shapefile {shapefile_path}')
                    gdf = gpd.read_file(shapefile_path)
                    logging.debug('Shapefile berhasil dimuat.')

                    data_clustering = result[['Cluster']].reset_index().rename(columns={'Lokasi': 'provinsi'})
                    logging.debug('Terapkan kamus penyesuaian untuk nama provinsi.')
                    data_clustering['provinsi'] = data_clustering['provinsi'].replace(kamus_penyesuaian)

                    gdf_provinsi = gdf.dissolve(by=merge_on)
                    logging.debug('Shapefile digabungkan berdasarkan kolom merge_on.')
                    gdf_provinsi = gdf_provinsi.merge(data_clustering, left_on=merge_on, right_on='provinsi', how='left')
                    gdf_provinsi['color'] = gdf_provinsi['Cluster'].map(color_map).fillna('lightgrey')
                    logging.debug('Data clustering berhasil digabungkan dengan shapefile.')

                    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
                    gdf_provinsi.plot(ax=ax, color=gdf_provinsi['color'], alpha=0.7, edgecolor='black')
                    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
                    logging.debug('Peta berhasil digambar.')

                    if not is_kabupaten:
                        logging.debug('Menambahkan label untuk setiap provinsi.')
                        for x, y, label in zip(gdf_provinsi.geometry.centroid.x, gdf_provinsi.geometry.centroid.y, gdf_provinsi['provinsi']):
                            ax.text(x, y, label, fontsize=8, ha='center', va='center', color='black')

                    logging.debug('Menambahkan interpretasi cluster pada peta.')
                    interpretations_text = "\n".join([f"Cluster {cluster}: {label}" for cluster, label in interpretations.items()])
                    plt.figtext(0.02, 0.98, interpretations_text, wrap=True, horizontalalignment='left', verticalalignment='top', fontsize=10, bbox={"facecolor": "white", "alpha": 0.5, "pad": 5})

                    plt.legend(handles=legend_patches, loc='lower left', bbox_to_anchor=(1, 0), fontsize='small')
                    plt.title("Visualisasi Hasil Clustering Produktivitas Padi di Indonesia")
                    plt.xlabel("Longitude")
                    plt.ylabel("Latitude")
                    plt.savefig('static/map.png')
                    plt.close()
                    logging.debug('Peta berhasil disimpan.')
                except Exception as e:
                    logging.error('Error saat membuat peta: %s', e)
                    flash('An error occurred while creating the map.')

                # Simpan hasil clustering ke file Excel
                try:
                    output = result[['Cluster']].reset_index().rename(columns={'Lokasi': 'Daerah'})
                    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.xlsx')
                    output.to_excel(output_path, index=False)
                    # flash('Download output.xlsx')
                except Exception as e:
                    logging.error('Error: %s', e)
                    flash('An error occurred while saving the results.')

            except Exception as e:
                logging.error('Error saat memproses data: %s', e)
                flash('An error occurred while processing the data.')
            finally:
                logging.debug('Menghapus file sementara')
                if os.path.exists(filepath):
                    os.remove(filepath)

            return render_template('index.html', result=True, keterangan=keterangan)
    return redirect(url_for('home'))
                    
@app.route('/download-pdf')
def download_pdf():
    # Ambil jumlah cluster dan algoritma dari session
    clusters = session.get('clusters')
    algorithm = session.get('algorithm')

    # Mengubah format nama algoritma
    if algorithm == 'kmeans':
        algorithm_name = 'K-Means Clustering'
    elif algorithm == 'fuzzy':
        algorithm_name = 'Fuzzy C-Means'

    # Membuat instance PDF
    pdf = FPDF()
    pdf.add_page()

    # Menambahkan judul
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Hasil Clustering Produktivitas Padi Menggunakan Algoritma {algorithm_name} dengan {clusters} Cluster", 0, 'C')

    # Menambahkan gambar visualisasi plot distribusi
    pdf.ln(10)
    pdf.image('static/distribution.png', x=20, w=170)

    # Menambahkan gambar visualisasi peta dengan ukuran lebih besar
    pdf.add_page()
    pdf.image('static/map.png', x=5, w=200)

    # Menambahkan tabel cluster
    result = pd.read_excel(os.path.join(app.config['UPLOAD_FOLDER'], 'output.xlsx'))
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    col_width = pdf.w / 4.5
    row_height = pdf.font_size
    table_width = col_width * result.shape[1]
    margin_left = (pdf.w - table_width) / 2

    pdf.ln(10)
    pdf.multi_cell(0, 10, "Tabel Hasil Clustering:", 0, 'C')
    pdf.ln(5)

    for row in result.itertuples(index=False):
        pdf.set_x(margin_left)  # Atur margin kiri sebelum menambahkan sel tabel
        for item in row:
            pdf.cell(col_width, row_height*2, str(item), border=1, ln=0, align='C')
        pdf.ln(row_height*2)
    
    # Menyimpan file PDF
    pdf_output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'hasil_clustering.pdf')
    pdf.output(pdf_output_path)

    return send_file(pdf_output_path, as_attachment=True, download_name='hasil_clustering.pdf')

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
