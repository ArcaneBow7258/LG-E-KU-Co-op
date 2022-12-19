otterdf = trimbleData["U1C23"].filter(((trimbleData["U1C23"].tag == 1501230004) | (trimbleData["U1C23"].tag == 1501230005)) & (trimbleData["U1C23"].time >= "2021-6-25 01:00:00") & (trimbleData["U1C23"].time < "2021-6-25 02:00:00"))
                
b = otterdf.toPandas()
df_pivot = b.pivot(index='time', columns='tag',values = 'value')
df_feat = df_pivot.drop(labels=1501230004, axis=1)
X_train, X_test, y_train, y_test = train_test_split(df_feat, df_pivot[1501230004])
ridge = Ridge(alpha = 0.1, normalize = True)
mod_ridge = ridge.fit(X_train, y_train)
ridge_predicted = mod_ridge.predict(X_test)
expected = y_test

plt.scatter(expected, ridge_predicted)
plt.xlabel('True MW')
plt.ylabel('Predicted MW')
plt.plot([0, 50], [0, 50], '--k')
plt.savefig('/u00/djangoTestSiteRyan/DashboardNew/DashboardWebappApp/static/pics/p1.png')
                