import random
import cgi
import json
import tempfile

import six

import ckan.plugins.toolkit as toolkit
from frictionless_ckan_mapper import frictionless_to_ckan as converter
from werkzeug.datastructures import FileStorage

import datapackage


def package_create_from_datapackage(context, data_dict):
    '''Create a new dataset (package) from a Data Package file.

    :param url: url of the datapackage (optional if `upload` is defined)
    :type url: string
    :param upload: the uploaded datapackage (optional if `url` is defined)
    :type upload: cgi.FieldStorage
    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'`` (optional, default:
        datapackage's name concatenated with a random string to avoid
        name collisions)
    :type name: string
    :param private: the visibility of the new dataset
    :type private: bool
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string
    '''
    url = data_dict.get('url')
    upload = data_dict.get('upload')

    if not url and not _upload_attribute_is_valid(upload):
        msg = {'url': ['you must define either a url or upload attribute']}
        raise toolkit.ValidationError(msg)

    dp = _load_and_validate_datapackage(url=url, upload=upload)

    dataset_dict = converter.package(dp.to_dict())

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org

    private = data_dict.get('private')
    if private:
        dataset_dict['private'] = toolkit.asbool(private)

    name = data_dict.get('name')
    if name:
        dataset_dict['name'] = name

    accessRights = data_dict.get('accessRights')
    if accessRights:
        dataset_dict['accessRights'] = accessRights

    accrualPeriodicity = data_dict.get('accrualPeriodicity')
    if accrualPeriodicity:
        dataset_dict['accrualPeriodicity'] = accrualPeriodicity

    id_dds = data_dict.get('id_dds')
    if id_dds:
        dataset_dict['id_dds'] = id_dds

    id_indikator_mms = data_dict.get('id_indikator_mms')
    if id_indikator_mms:
        dataset_dict['id_indikator_mms'] = id_indikator_mms

    id_sds = data_dict.get('id_sds')
    if id_sds:
        dataset_dict['id_sds'] = id_sds

    jenis = data_dict.get('jenis')
    if jenis:
        dataset_dict['jenis'] = jenis

    satuan = data_dict.get('satuan')
    if satuan:
        dataset_dict['satuan'] = satuan

    ukuran = data_dict.get('ukuran')
    if ukuran:
        dataset_dict['ukuran'] = ukuran

    prioritas_tahun = data_dict.get('prioritas_tahun')
    if prioritas_tahun:
        dataset_dict['prioritas_tahun'] = prioritas_tahun

    publisher_type = data_dict.get('publisher_type')
    if publisher_type:
        dataset_dict['publisher_type'] = publisher_type

    publishing_status = data_dict.get('publishing_status')
    if publishing_status:
        dataset_dict['publishing_status'] = publishing_status

    theme = data_dict.get('theme')
    if theme:
        dataset_dict['theme'] = theme

    id_msind = data_dict.get('id_msind')
    if id_msind:
        dataset_dict['id_msind'] = id_msind

    id_mskeg = data_dict.get('id_mskeg')
    if id_mskeg:
        dataset_dict['id_mskeg'] = id_mskeg

    apakah_indikator_komposit = data_dict.get('apakah_indikator_komposit')
    if apakah_indikator_komposit:
        dataset_dict['apakah_indikator_komposit'] = apakah_indikator_komposit

    indikator_prioritas = data_dict.get('indikator_prioritas')
    if indikator_prioritas:
        dataset_dict['indikator_prioritas'] = indikator_prioritas

    interpretasi = data_dict.get('interpretasi')
    if interpretasi:
        dataset_dict['interpretasi'] = interpretasi

    variabel_disaggregasi = data_dict.get('variabel_disaggregasi')
    if variabel_disaggregasi:
        dataset_dict['variabel_disaggregasi'] = variabel_disaggregasi

    kodereferensi = data_dict.get('kodereferensi')
    if kodereferensi:
        dataset_dict['kodereferensi'] = kodereferensi

    kriteria_prioritas = data_dict.get('kriteria_prioritas')
    if kriteria_prioritas:
        dataset_dict['kriteria_prioritas'] = kriteria_prioritas

    level_estimasi = data_dict.get('level_estimasi')
    if level_estimasi:
        dataset_dict['level_estimasi'] = level_estimasi

    metode_perhitungan = data_dict.get('metode_perhitungan')
    if metode_perhitungan:
        dataset_dict['metode_perhitungan'] = metode_perhitungan

    rumus = data_dict.get('rumus')
    if rumus:
        dataset_dict['rumus'] = rumus

    id_kegiatan_mms = data_dict.get('id_kegiatan_mms')
    if id_kegiatan_mms:
        dataset_dict['id_kegiatan_mms'] = id_kegiatan_mms

    id_kegiatan = data_dict.get('id_kegiatan')
    if id_kegiatan:
        dataset_dict['id_kegiatan'] = id_kegiatan

    judul_kegiatan = data_dict.get('judul_kegiatan')
    if judul_kegiatan:
        dataset_dict['judul_kegiatan'] = judul_kegiatan

    tahun_kegiatan = data_dict.get('tahun_kegiatan')
    if tahun_kegiatan:
        dataset_dict['tahun_kegiatan'] = tahun_kegiatan

    jenis_statistik = data_dict.get('jenis_statistik')
    if jenis_statistik:
        dataset_dict['jenis_statistik'] = jenis_statistik

    cara_pengumpulan_data = data_dict.get('cara_pengumpulan_data')
    if cara_pengumpulan_data:
        dataset_dict['cara_pengumpulan_data'] = cara_pengumpulan_data

    sektor_kegiatan = data_dict.get('sektor_kegiatan')
    if sektor_kegiatan:
        dataset_dict['sektor_kegiatan'] = sektor_kegiatan

    identitas_rekomendasi = data_dict.get('identitas_rekomendasi')
    if identitas_rekomendasi:
        dataset_dict['identitas_rekomendasi'] = identitas_rekomendasi

    i_instansi_penyelanggara = data_dict.get('i_instansi_penyelanggara')
    if i_instansi_penyelanggara:
        dataset_dict['i_instansi_penyelanggara'] = i_instansi_penyelanggara

    i_alamat = data_dict.get('i_alamat')
    if i_alamat:
        dataset_dict['i_alamat'] = i_alamat

    i_telepon = data_dict.get('i_telepon')
    if i_telepon:
        dataset_dict['i_telepon'] = i_telepon

    i_email = data_dict.get('i_email')
    if i_email:
        dataset_dict['i_email'] = i_email

    i_faksimile = data_dict.get('i_faksimile')
    if i_faksimile:
        dataset_dict['i_faksimile'] = i_faksimile

    ii_unit_eselon2 = data_dict.get('ii_unit_eselon2')
    if ii_unit_eselon2:
        dataset_dict['ii_unit_eselon2'] = ii_unit_eselon2

    ii_pj_nama = data_dict.get('ii_pj_nama')
    if ii_pj_nama:
        dataset_dict['ii_pj_nama'] = ii_pj_nama

    ii_pj_jabatan = data_dict.get('ii_pj_jabatan')
    if ii_pj_jabatan:
        dataset_dict['ii_pj_jabatan'] = ii_pj_jabatan

    ii_pj_alamat = data_dict.get('ii_pj_alamat')
    if ii_pj_alamat:
        dataset_dict['ii_pj_alamat'] = ii_pj_alamat

    ii_pj_telepon = data_dict.get('ii_pj_telepon')
    if ii_pj_telepon:
        dataset_dict['ii_pj_telepon'] = ii_pj_telepon

    ii_pj_email = data_dict.get('ii_pj_email')
    if ii_pj_email:
        dataset_dict['ii_pj_email'] = ii_pj_email

    ii_pj_faksimile = data_dict.get('ii_pj_faksimile')
    if ii_pj_faksimile:
        dataset_dict['ii_pj_faksimile'] = ii_pj_faksimile

    iii_latar_belakang_kegiatan = data_dict.get('iii_latar_belakang_kegiatan')
    if iii_latar_belakang_kegiatan:
        dataset_dict['iii_latar_belakang_kegiatan'] = iii_latar_belakang_kegiatan

    iii_tujuan_kegiatan = data_dict.get('iii_tujuan_kegiatan')
    if iii_tujuan_kegiatan:
        dataset_dict['iii_tujuan_kegiatan'] = iii_tujuan_kegiatan

    iv_kegiatan_ini_dilakukan = data_dict.get('iv_kegiatan_ini_dilakukan')
    if iv_kegiatan_ini_dilakukan:
        dataset_dict['iv_kegiatan_ini_dilakukan'] = iv_kegiatan_ini_dilakukan

    iv_frekuensi_penyelanggara = data_dict.get('iv_frekuensi_penyelanggara')
    if iv_frekuensi_penyelanggara:
        dataset_dict['iv_frekuensi_penyelanggara'] = iv_frekuensi_penyelanggara

    iv_tipe_pengumpulan_data = data_dict.get('iv_tipe_pengumpulan_data')
    if iv_tipe_pengumpulan_data:
        dataset_dict['iv_tipe_pengumpulan_data'] = iv_tipe_pengumpulan_data

    iv_cakupan_wilayah_pengumpulan_data = data_dict.get('iv_cakupan_wilayah_pengumpulan_data')
    if iv_cakupan_wilayah_pengumpulan_data:
        dataset_dict['iv_cakupan_wilayah_pengumpulan_data'] = iv_cakupan_wilayah_pengumpulan_data

    iv_metode_pengumpulan_data = data_dict.get('iv_metode_pengumpulan_data')
    if iv_metode_pengumpulan_data:
        dataset_dict['iv_metode_pengumpulan_data'] = iv_metode_pengumpulan_data

    iv_sarana_pengumpulan_data = data_dict.get('iv_sarana_pengumpulan_data')
    if iv_sarana_pengumpulan_data:
        dataset_dict['iv_sarana_pengumpulan_data'] = iv_sarana_pengumpulan_data

    iv_unit_pengumpulan_data = data_dict.get('iv_unit_pengumpulan_data')
    if iv_unit_pengumpulan_data:
        dataset_dict['iv_unit_pengumpulan_data'] = iv_unit_pengumpulan_data

    v_jenis_rancangan_sampel = data_dict.get('v_jenis_rancangan_sampel')
    if v_jenis_rancangan_sampel:
        dataset_dict['v_jenis_rancangan_sampel'] = v_jenis_rancangan_sampel

    v_metode_pemilihan_sampel_tahap_terakhir = data_dict.get('v_metode_pemilihan_sampel_tahap_terakhir')
    if v_metode_pemilihan_sampel_tahap_terakhir:
        dataset_dict['v_metode_pemilihan_sampel_tahap_terakhir'] = v_metode_pemilihan_sampel_tahap_terakhir

    v_metode_yang_digunakan = data_dict.get('v_metode_yang_digunakan')
    if v_metode_yang_digunakan:
        dataset_dict['v_metode_yang_digunakan'] = v_metode_yang_digunakan

    v_kerangka_sampel_tahap_terakhir = data_dict.get('v_kerangka_sampel_tahap_terakhir')
    if v_kerangka_sampel_tahap_terakhir:
        dataset_dict['v_kerangka_sampel_tahap_terakhir'] = v_kerangka_sampel_tahap_terakhir
        
    v_fraksi_sampel_keseluruhan = data_dict.get('v_fraksi_sampel_keseluruhan')
    if v_fraksi_sampel_keseluruhan:
        dataset_dict['v_fraksi_sampel_keseluruhan'] = v_fraksi_sampel_keseluruhan

    v_nilai_perkiraan_sampling_error_variabel_utama = data_dict.get('v_nilai_perkiraan_sampling_error_variabel_utama')
    if v_nilai_perkiraan_sampling_error_variabel_utama:
        dataset_dict['v_nilai_perkiraan_sampling_error_variabel_utama'] = v_nilai_perkiraan_sampling_error_variabel_utama

    v_unit_sampel = data_dict.get('v_unit_sampel')
    if v_unit_sampel:
        dataset_dict['v_unit_sampel'] = v_unit_sampel

    v_unit_observasi = data_dict.get('v_unit_observasi')
    if v_unit_observasi:
        dataset_dict['v_unit_observasi'] = v_unit_observasi

    vi_apakah_melakukan_uji_coba = data_dict.get('vi_apakah_melakukan_uji_coba')
    if vi_apakah_melakukan_uji_coba:
        dataset_dict['vi_apakah_melakukan_uji_coba'] = vi_apakah_melakukan_uji_coba

    vi_metode_pemeriksaan_kualitas_pengumpulan_data = data_dict.get('vi_metode_pemeriksaan_kualitas_pengumpulan_data')
    if vi_metode_pemeriksaan_kualitas_pengumpulan_data:
        dataset_dict['vi_metode_pemeriksaan_kualitas_pengumpulan_data'] = vi_metode_pemeriksaan_kualitas_pengumpulan_data

    vi_apakah_melakukan_penyesuaian_nonrespon = data_dict.get('vi_apakah_melakukan_penyesuaian_nonrespon')
    if vi_apakah_melakukan_penyesuaian_nonrespon:
        dataset_dict['vi_apakah_melakukan_penyesuaian_nonrespon'] = vi_apakah_melakukan_penyesuaian_nonrespon

    vi_petugas_pengumpulan_data = data_dict.get('vi_petugas_pengumpulan_data')
    if vi_petugas_pengumpulan_data:
        dataset_dict['vi_petugas_pengumpulan_data'] = vi_petugas_pengumpulan_data

    vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data = data_dict.get('vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data')
    if vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data:
        dataset_dict['vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data'] = vi_persyaratan_pendidikan_terendah_petugas_pengumpulan_data

    vi_jumlah_petugas_supervisor = data_dict.get('vi_jumlah_petugas_supervisor')
    if vi_jumlah_petugas_supervisor:
        dataset_dict['vi_jumlah_petugas_supervisor'] = vi_jumlah_petugas_supervisor

    vi_jumlah_petugas_enumerator = data_dict.get('vi_jumlah_petugas_enumerator')
    if vi_jumlah_petugas_enumerator:
        dataset_dict['vi_jumlah_petugas_enumerator'] = vi_jumlah_petugas_enumerator

    vi_apakah_melakukan_pelatihan_petugas = data_dict.get('vi_apakah_melakukan_pelatihan_petugas')
    if vi_apakah_melakukan_pelatihan_petugas:
        dataset_dict['vi_apakah_melakukan_pelatihan_petugas'] = vi_apakah_melakukan_pelatihan_petugas

    vii_tahapan_pengolahan_data = data_dict.get('vii_tahapan_pengolahan_data')
    if vii_tahapan_pengolahan_data:
        dataset_dict['vii_tahapan_pengolahan_data'] = vii_tahapan_pengolahan_data

    vii_metode_analisis = data_dict.get('vii_metode_analisis')
    if vii_metode_analisis:
        dataset_dict['vii_metode_analisis'] = vii_metode_analisis

    vii_unit_analisis = data_dict.get('vii_unit_analisis')
    if vii_unit_analisis:
        dataset_dict['vii_unit_analisis'] = vii_unit_analisis

    vii_tingkat_penyajian_hasil_analisis = data_dict.get('vii_tingkat_penyajian_hasil_analisis')
    if vii_tingkat_penyajian_hasil_analisis:
        dataset_dict['vii_tingkat_penyajian_hasil_analisis'] = vii_tingkat_penyajian_hasil_analisis

    viii_ketersediaan_produk_tercetak = data_dict.get('viii_ketersediaan_produk_tercetak')
    if viii_ketersediaan_produk_tercetak:
        dataset_dict['viii_ketersediaan_produk_tercetak'] = viii_ketersediaan_produk_tercetak

    viii_ketersediaan_produk_digital = data_dict.get('viii_ketersediaan_produk_digital')
    if viii_ketersediaan_produk_digital:
        dataset_dict['viii_ketersediaan_produk_digital'] = viii_ketersediaan_produk_digital

    viii_ketersediaan_produk_mikrodata = data_dict.get('viii_ketersediaan_produk_mikrodata')
    if viii_ketersediaan_produk_mikrodata:
        dataset_dict['viii_ketersediaan_produk_mikrodata'] = viii_ketersediaan_produk_mikrodata

    produsen_data_name = data_dict.get('produsen_data_name')
    if produsen_data_name:
        dataset_dict['produsen_data_name'] = produsen_data_name

    produsen_data_city_code = data_dict.get('produsen_data_city_code')
    if produsen_data_city_code:
        dataset_dict['produsen_data_city_code'] = produsen_data_city_code

    produsen_data_province_code = data_dict.get('produsen_data_province_code')
    if produsen_data_province_code:
        dataset_dict['produsen_data_province_code'] = produsen_data_province_code

    total_msvar = data_dict.get('total_msvar')
    if total_msvar:
        dataset_dict['total_msvar'] = total_msvar

    total_msind = data_dict.get('total_msind')
    if total_msind:
        dataset_dict['total_msind'] = total_msind

    submission_period = data_dict.get('submission_period')
    if submission_period:
        dataset_dict['submission_period'] = submission_period

    resources = dataset_dict.get('resources', [])
    if resources:
        del dataset_dict['resources']

    # Create as draft by default so if there's any issue on creating the
    # resources and we're unable to purge the dataset, at least it's not shown.
    dataset_dict['state'] = 'draft'
    res = _package_create_with_unique_name(context, dataset_dict, name)

    dataset_id = res['id']

    if resources:
        try:
            _create_resources(dataset_id, context, resources)
            res = toolkit.get_action('package_show')(
                context, {'id': dataset_id})
        except Exception as e:
            try:
                toolkit.get_action('package_delete')(
                    context, {'id': dataset_id})
            except Exception as e2:
                six.raise_from(e, e2)
            else:
                raise e

    res['state'] = 'active'
    return toolkit.get_action('package_update')(context, res)


def _load_and_validate_datapackage(url=None, upload=None):
    try:

        if _upload_attribute_is_valid(upload):
            dp = datapackage.DataPackage(upload.file)
        else:

            dp = datapackage.DataPackage(url)

        dp.validate()
    except (datapackage.exceptions.DataPackageException,
            datapackage.exceptions.SchemaError,
            datapackage.exceptions.ValidationError) as e:

        msg = {'datapackage': e}
        raise toolkit.ValidationError(msg)

    if not dp.safe():
        msg = {'datapackage': ['the Data Package has unsafe attributes']}
        raise toolkit.ValidationError(msg)

    return dp


def _package_create_with_unique_name(context, dataset_dict, name=None):
    res = None
    if name:
        dataset_dict['name'] = name

    try:
        res = toolkit.get_action('package_create')(context, dataset_dict)
    except toolkit.ValidationError as e:
        if not name and \
           'That URL is already in use.' in e.error_dict.get('name', []):
            random_num = random.randint(0, 9999999999)
            name = '{name}-{rand}'.format(name=dataset_dict.get('name', 'dp'),
                                          rand=random_num)
            dataset_dict['name'] = name
            res = toolkit.get_action('package_create')(context, dataset_dict)
        else:
            raise

    return res


def _create_resources(dataset_id, context, resources):
    for resource in resources:
        resource['package_id'] = dataset_id
        if resource.get('data'):
            _create_and_upload_resource_with_inline_data(context, resource)
        elif resource.get('path'):
            _create_and_upload_local_resource(context, resource)
        else:
            toolkit.get_action('resource_create')(context, resource)

        #return toolkit.redirect_to("dataset.edit", id=dataset_id)


def _create_and_upload_resource_with_inline_data(dataset_id, context, resource):
    prefix = resource.get('name', 'tmp')
    data = resource['data']

    del resource['data']
    if not isinstance(data, six.string_types):
        data = json.dumps(data, indent=2)

    with tempfile.NamedTemporaryFile(prefix=prefix) as f:
        f.write(six.binary_type(data, 'utf-8'))
        f.seek(0)

        _create_and_upload_resource(context, resource, f)

        #return toolkit.redirect_to("dataset.edit", id=dataset_id)


def _create_and_upload_local_resource(context, resource):
    path = resource['path']
    del resource['path']
    if isinstance(path, list):
        path = path[0]
    try:
        with open(path, 'r') as f:
            _create_and_upload_resource(context, resource, f)
    except IOError:
        msg = {'datapackage': [(
            "Couldn't create some of the resources."
            " Please make sure that all resources' files are accessible."
        )]}
        raise toolkit.ValidationError(msg)


def _create_and_upload_resource(dataset_id, context, resource, the_file):
    resource['url'] = 'url'
    resource['url_type'] = 'upload'
    resource['upload'] = FileStorage(the_file, the_file.name, the_file.name)

    toolkit.get_action('resource_create')(context, resource)

    #return toolkit.redirect_to("dataset.edit", id=dataset_id)


def _upload_attribute_is_valid(upload):
    return hasattr(upload, 'file') and hasattr(upload.file, 'read')


class _UploadLocalFileStorage(FileStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp

        #return toolkit.redirect_to("dataset.edit", id=package_id)
