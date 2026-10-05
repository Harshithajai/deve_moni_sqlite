export const tokenKey = 'devcare_token';
export const roleKey = 'devcare_role';
export const userIdKey = 'devcare_user_id';

export function isAuthenticated() {
  return Boolean(localStorage.getItem(tokenKey));
}

export function getRole() {
  return localStorage.getItem(roleKey);
}

export function getUserId() {
  return localStorage.getItem(userIdKey);
}

export function logout() {
  localStorage.removeItem(tokenKey);
  localStorage.removeItem(roleKey);
  localStorage.removeItem(userIdKey);
}
