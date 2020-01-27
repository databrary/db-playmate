# Databrary module

# Import dependencies
import requests
import pandas
import keyring
import io
import re
from tqdm import tqdm

class Databrary:
  PLAY_VOLUME = 899
  def __init__(self, login_username):
      """The password must be stored on the system keychain"""
      self.login_db(login_username)

  #-----------------------------------------------------------------------------
  def assign_constants(self, vb = False):
    "Download Databrary contants from API"

    # Check parameters
    if (not(isinstance(vb, bool))):
      print("vb must be Boolean.")
      return('')

    constants_url = "https://nyu.databrary.org/api/constants"

    if vb:
      print("Sending GET request to " + constants_url + "\n")

    r = self.session.get(constants_url)
    if (r.status_code == 200):
      if (type == 'all'):
        return(r.content)
      else:
        # Convert content to data.frame
        df = pandas.read_json(r.content, typ = 'series')
        return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #-----------------------------------------------------------------------------
  # Access Databrary API to get current system stats
  def get_db_stats(self, type = "all", vb = False):
    "Current stats from Databrary API"

    # Check parameters
    if (not(isinstance(type, str))):
      print("type must be a string.")
      return('')
    if (not(isinstance(vb, bool))):
      print("vb must be Boolean.")
      return('')

    stats_activity_url = "https://nyu.databrary.org/api/activity"

    if vb:
      print("Sending GET request to " + stats_activity_url + "\n")
    r = self.session.get(stats_activity_url)

    if (r.status_code == 200):
      if (type == 'all'):
        return(r.content)
      else:
        # Convert content to data.frame
        df = pandas.read_json(r.content, typ = 'series')
        return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #-----------------------------------------------------------------------------
  # login to Databrary
  # TODO(ROG): Saving cookies!
  def login_db(self, username = '', vb = False, stored_credentials = False, system_credentials = True, return_resp = False):
    "Log in to Databrary"


    # Check parameters
    if (not(isinstance(username, str))):
      print("username must be a string.")
      return('')
    if (not(isinstance(vb, bool))):
      print("vb must be Boolean.")
      return('')
    if (not(isinstance(stored_credentials, bool))):
      print("stored_credentials must be Boolean.")
      return('')
    if (not(isinstance(system_credentials, bool))):
      print("system_credentials must be Boolean.")
      return('')

    login_url = "https://nyu.databrary.org/api/user/login"

    if (stored_credentials):
      if(vb):
        print("Using stored credentials.")
    elif (system_credentials):
      if (username == ''):
        print("Please enter your Databrary user ID (email).")
        username = input("User ID: ")
      if (keyring.get_keyring() != ''):
          kl = keyring.get_password("databrary", username)
          if (kl != 'None'):
            pw = kl
          else:
            if (vb):
              print("No password for user: ", username, "\n")
              return('')
      else:
        if (vb):
          print("No stored credentials for user: ", username, "\n")
          return('')
    else:
      # Get login credentials
      username = input("User ID: ")
      pw = input("Password: ")

    # Check login credentials
    if (not(isinstance(username, str))):
      print("username must be a string.")
      return('')
    if (not(isinstance(pw, str))):
      print("Password must be a string")
      return('')

    # POST request
    payload = {"email": username, "password": pw}
    if (vb):
      print("Sending GET request to ", login_url)

    self.session = requests.Session()
    r = self.session.post(login_url, data = payload)

    if (r.status_code == 200):
      print("Logged in.")
      if (return_resp):
        return(r.text)
    else:
      print("Log in failed with HTTP status " + r.status_code + "\n")

    return r

  #------------------------------------------------------------------------------
  def is_institution(self, party_id = 8, vb = False, return_JSON = False):

    # Check parameters
    if isinstance(party_id, list):
      print("party_id must be single scalar value")
      return('')
    if not(isinstance(party_id, int)) or (party_id <= 0):
      print("party_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    party_url = "https://nyu.databrary.org/api/party/" + str(party_id)

    if (vb):
      message(paste0("Sending GET to ", party_url))
    r = self.session.get(party_url)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      if return_JSON:
        return(r.text)
      # Otherwise, convert JSON to data frame
      df = pandas.read_json(r.content, typ = 'series')
      return('institution' in df.index)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def is_person(self, party_id = 7, vb = False):
    r = not(is_institution(party_id = party_id, vb = vb))
    return(r)

  #------------------------------------------------------------------------------
  def get_institution(self, party_id = 8, vb = False, return_JSON = False):
    "Download data about an institution"

    # Check parameters
    if isinstance(party_id, list):
      print("party_id must be single scalar value")
      return('')
    if not(isinstance(party_id, int)) or (party_id <= 0):
      print("party_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')
    if not(isinstance(return_JSON, bool)):
      print("return_JSON must be Boolean")
      return('')

    party_url = "https://nyu.databrary.org/api/party/" + str(party_id)

    if (vb):
      message(paste0("Sending GET to ", party_url))
    r = self.session.get(party_url)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      if return_JSON:
        return(r.text)
      # Otherwise, convert JSON to data frame
      df = pandas.read_json(r.content, typ = 'series')
      if not('institution' in df.index):
        print("Party ID " + party_id + " is not an institution.")
        return('')
      return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def get_person(self, party_id = 7, vb = False, return_JSON = False):
    "Downloads metadata about a person."

    # Check parameters
    if isinstance(party_id, list):
      print("party_id must be single scalar value")
      return('')
    if not(isinstance(party_id, int)) or (party_id <= 0):
      print("party_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')
    if not(isinstance(return_JSON, bool)):
      print("return_JSON must be Boolean")
      return('')

    party_url = "https://nyu.databrary.org/api/party/" + str(party_id)

    if (vb):
      message(paste0("Sending GET to ", party_url))
    r = self.session.get(party_url)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      if return_JSON:
        return(r.text)
      # Otherwise, convert JSON to data frame
      df = pandas.read_json(r.content, typ = 'series')
      if not('prename' in df.index):
        print("Party ID " + party_id + " is not a person.")
        return('')
      return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def download_party(self, party_id = 7, vb = False, return_JSON = False):

    # Check parameters
    if isinstance(party_id, list):
      print("party_id must be single scalar value")
      return('')
    if not(isinstance(party_id, int)) or (party_id <= 0):
      print("party_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')
    if not(isinstance(return_JSON, bool)):
      print("return_JSON must be Boolean")
      return('')

    party_url = "https://nyu.databrary.org/api/party/" + str(party_id)

    if (vb):
      print("Sending GET to " + party_url)
    r = self.session.get(party_url)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      if return_JSON:
        return(r.text)
      # Otherwise, convert JSON to data frame
      df = pandas.read_json(r.content, typ = 'series')
      return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def download_session_csv(self, vol_id = 1, to_df = True, return_response = False, vb = False):

    # Parameter checking
    if isinstance(vol_id, list):
      stop("vol_id must have length 1.")
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if not(isinstance(to_df, bool)):
      print("vb must be Boolean")
      return('')
    if not(isinstance(return_response, bool)):
      print("return_response must be Boolean")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    request_url = "https://nyu.databrary.org/volume/" + str(vol_id) + "/csv"

    r = self.session.get(request_url)
    print("Sending GET to " + request_url)
    if (r.status_code == 200):
      if(to_df):
        bytes_content = io.BytesIO(r.content)
        df = pandas.read_csv(bytes_content)
        return(df)
      else:
        return(r.content)
    else:
      print('Download Failed, HTTP status ' + str(r.status_code))
      if (return_response):
        return(r.status_code)

  #------------------------------------------------------------------------------
  def get_supported_file_types(self, vb = False):
    "Extracts Databrary supported file types."

    # Check parameters
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    c = assign_constants(vb = vb)
    fts = c['format']
    df = pandas.DataFrame.from_dict(fts)
    return(df)

  #------------------------------------------------------------------------------
  def list_sessions_in_volume(self, vol_id = 1, vb = False):
    "List the slots/sessions in a specified volume"

    # Check parameters
    if isinstance(vol_id, list):
      print("vol_id must be single scalar value")
      return('')
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    vol_url = "https://nyu.databrary.org/api/volume/" + str(vol_id)

    if (vb):
      print("Sending GET to ", vol_url)
    r = self.session.get(vol_url)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      df = pandas.read_json(r.content, typ = 'series')
      return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def download_containers_records(self, vol_id = 2, convert_JSON = True, vb = False):
    """ Download data about the containers (sessions/slots) in a given volume"""
    # Check parameters
    if isinstance(vol_id, list):
      stop("vol_id must be a single, scalar value.")
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if not(isinstance(convert_JSON, bool)):
      print("vb must be Boolean")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    url_cont_rec = "https://nyu.databrary.org/api/volume/" + str(vol_id) + "?containers&records"
    if (vb):
      print("Sending GET to ", url_cont_rec)
    r = self.session.get(url_cont_rec)
    if (r.status_code == 200):
      if vb:
        print("Success.")
      if convert_JSON:
        df = pandas.read_json(r.content, typ = 'series')
        return(df)
      else:
        return(r.text)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

  #------------------------------------------------------------------------------
  def download_asset(self, vol_id = 1, session_id = 9807, asset_id = 1, vb = False, download_dir = "./"):

    # Check parameters
    if isinstance(vol_id, list):
      stop("vol_id must be a single, scalar value.")
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if isinstance(session_id, list):
      stop("session_id must be a single, scalar value.")
    if not(isinstance(session_id, int)) or (session_id <= 0):
      print("session_id must be an integer > 0")
      return('')
    if isinstance(asset_id, list):
      stop("asset_id must be a single, scalar value.")
    if not(isinstance(asset_id, int)) or (asset_id <= 0):
      print("asset_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    url = "https://nyu.databrary.org/slot/" + str(session_id) + "/asset/" + str(asset_id) + "/download?inline=false"
    if (vb):
      print("Sending GET to ", url)
      filename = "{}/{}-{}-{}.mp4".format(download_dir, vol_id, session_id, asset_id)
      with self.session.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        block_size = 1024 #1 Kibibyte
        t=tqdm(total=total_size, unit='iB', unit_scale=True)
        with open(filename, 'wb') as f:
          for chunk in r.iter_content(chunk_size=8192):
            if chunk:
              t.update(len(chunk))
              f.write(chunk)
          if (r.status_code == 200):
              if vb:
                print("Success!")
                return(df)
              else:
                print("Download failed with HTTP status " + r.status_code + "\n")
                return('')

  def download_asset_stream(self, vol_id = 1, session_id = 9807, asset_id = 1, vb = False):

    def iterable_to_stream(iterable, total_size, buffer_size=io.DEFAULT_BUFFER_SIZE):
      """
      Lets you use an iterable (e.g. a generator) that yields bytestrings as a read-only
      input stream.

      The stream implements Python 3's newer I/O API (available in Python 2's io module).
      For efficiency, the stream is buffered.
      """
      class IterStream(io.RawIOBase):
          def __init__(self):
              self.leftover = None
              self.t=tqdm(total=total_size, unit='iB', unit_scale=True)
          def readable(self):
              return True
          def readinto(self, b):
              try:
                l = len(b)  # We're supposed to return at most this much
                chunk = self.leftover or next(iterable)
                output, self.leftover = chunk[:l], chunk[l:]
                b[:len(output)] = output
                self.t.update(len(output))
                return len(output)
              except StopIteration as e:
                return 0    # indicate EOF
      return io.BufferedReader(IterStream(), buffer_size=buffer_size)

    # Check parameters
    if isinstance(vol_id, list):
      stop("vol_id must be a single, scalar value.")
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if isinstance(session_id, list):
      stop("session_id must be a single, scalar value.")
    if not(isinstance(session_id, int)) or (session_id <= 0):
      print("session_id must be an integer > 0")
      return('')
    if isinstance(asset_id, list):
      stop("asset_id must be a single, scalar value.")
    if not(isinstance(asset_id, int)) or (asset_id <= 0):
      print("asset_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    url = "https://nyu.databrary.org/slot/" + str(session_id) + "/asset/" + str(asset_id) + "/download?inline=false"
    print("Sending GET to ", url)
    r = self.session.get(url, stream=True)
    r.raise_for_status()
    total_size = int(r.headers.get('content-length', 0))
    print(total_size)
    d = r.headers['content-disposition']
    fname = re.findall("filename=(.+)", d)[0] 
    i = r.iter_content(8192)
    return iterable_to_stream(r.iter_content(8192), total_size), total_size, fname # Return the download stream for processing by another module (i.e., uploading to Box)
      

  #------------------------------------------------------------------------------
  def get_asset_segment_range(self, vol_id = 1, session_id = 9807, asset_id = 1, vb = False):

    # Check parameters
    if isinstance(vol_id, list):
      stop("vol_id must be a single, scalar value.")
    if not(isinstance(vol_id, int)) or (vol_id <= 0):
      print("vol_id must be an integer > 0")
      return('')
    if isinstance(session_id, list):
      stop("session_id must be a single, scalar value.")
    if not(isinstance(session_id, int)) or (session_id <= 0):
      print("session_id must be an integer > 0")
      return('')
    if isinstance(asset_id, list):
      stop("asset_id must be a single, scalar value.")
    if not(isinstance(asset_id, int)) or (asset_id <= 0):
      print("asset_id must be an integer > 0")
      return('')
    if not(isinstance(vb, bool)):
      print("vb must be Boolean")
      return('')

    url = "https://nyu.databrary.org/api/volume/" + str(vol_id) + "/slot/" + str(session_id) + "/asset/" + str(asset_id)
    if (vb):
      print("Sending GET to ", url)
    r = self.session.get(url)
    if (r.status_code == 200):
      if vb:
        print("Success!")
      df = pandas.read_json(r.content, typ = 'series')
      return(df)
    else:
      print("Download failed with HTTP status " + r.status_code + "\n")
      return('')

