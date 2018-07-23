/* Create Site */
LOCK TABLES `wagtailcore_site` WRITE;
DELETE FROM `wagtailcore_site`;
INSERT INTO `wagtailcore_site` VALUES (
    1,
    'localhost',
    18606,
    1,
    1,
    'edX'
);
UNLOCK TABLES;

/* Create Site Config */
LOCK TABLES `core_siteconfiguration` WRITE;
INSERT INTO
`core_siteconfiguration`
VALUES (
    1,
    'http://edx.devstack.lms:18000',
    '{\"SOCIAL_AUTH_EDX_OIDC_ID_TOKEN_DECRYPTION_KEY\":\"journals-secret\",\"SOCIAL_AUTH_EDX_OIDC_URL_ROOT\":\"http://edx.devstack.lms:18000/oauth2\",\"SOCIAL_AUTH_EDX_OIDC_ISSUERS\":[\"http://edx.devstack.lms:18000\"],\"SOCIAL_AUTH_EDX_OIDC_KEY\":\"journals-key\",\"SOCIAL_AUTH_EDX_OIDC_SECRET\":\"journals-secret\",\"SOCIAL_AUTH_EDX_OIDC_PUBLIC_URL_ROOT\":\"http://localhost:18000/oauth2\",\"SOCIAL_AUTH_EDX_OIDC_LOGOUT_URL\":\"http://localhost:18000/logout\",\"SOCIAL_AUTH_EDX_OIDC_ISSUER\":\"http://edx.devstack.lms:18000/oauth2\"}',
    1,
    'http://localhost:18000',
    'http://edx.devstack.discovery:18381/api/v1/',
    'http://edx.devstack.ecommerce:18130/api/v2/',
    'http://localhost:18130',
    'http://edx.devstack.discovery:18381/journal/api/v1/',
    'USD',
    'edx',
    'edx',
    'http://edx.devstack.ecommerce:18130/journal/api/v1',
    'http://localhost:1991'
);
UNLOCK TABLES;

/* Create base org */
LOCK TABLES `journals_organization` WRITE;
INSERT INTO `journals_organization` VALUES (1,'edX',1);
UNLOCK TABLES;

