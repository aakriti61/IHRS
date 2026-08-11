import axios from "axios";

// Each hospital now runs its OWN separate server -- Bir on port 8001
// (Postgres), TUTH on port 8002 (MySQL). Only one is "active" in this
// browser tab at a time (remembered in localStorage), switchable at
// runtime via setHospitalServer() below -- lets the SAME running
// frontend talk to whichever hospital's backend you're testing,
// without restarting anything or editing code.
export const HOSPITAL_SERVERS = {
  bir: { label: "Bir Hospital", url: "http://localhost:8001/api" },
  tuth: { label: "TUTH", url: "http://localhost:8002/api" },
};

const STORAGE_KEY = "ihrs_active_hospital_server";

export function getActiveHospitalServer() {
  return localStorage.getItem(STORAGE_KEY) || "bir";
}

export function setHospitalServer(key) {
  if (!HOSPITAL_SERVERS[key]) {
    throw new Error(`Unknown hospital server "${key}". Use one of: ${Object.keys(HOSPITAL_SERVERS).join(", ")}`);
  }
  localStorage.setItem(STORAGE_KEY, key);
  // Switching servers means switching identity entirely -- an
  // Bir-issued token means nothing to TUTH's server (separate
  // database, separate auth_token table). Clear the session so you
  // don't end up sending a stale token to the wrong hospital.
  localStorage.removeItem("ihrs_token");
  localStorage.removeItem("ihrs_user");
  localStorage.removeItem("ihrs_nhid");
}

const api = axios.create();

// baseURL is resolved PER REQUEST (not fixed once at creation) so that
// calling setHospitalServer() takes effect immediately on the next
// request, without reloading the page or recreating this instance.
api.interceptors.request.use((config) => {
  config.baseURL = HOSPITAL_SERVERS[getActiveHospitalServer()].url;

  const token = localStorage.getItem("ihrs_token");
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("ihrs_token");
      localStorage.removeItem("ihrs_user");
    }
    return Promise.reject(error);
  }
);

export default api;