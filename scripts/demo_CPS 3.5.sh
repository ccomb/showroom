#!/usr/bin/env bash
# PARAMS:name, login=admin, password, version=3.5.2, zope_version=2.9.12-final
set -e

# create a virtualenv
virtualenv -p python2.4 --no-site-packages --distribute sandbox

which lynx unzip xsltproc pdftohtml ghostscript unrtf wvHtml xlhtml ppthtml || exit 1

# dependencies
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ PIL==1.1.7
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ lxml==2.3.1
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ python-ldap==2.3.13
sandbox/bin/pip install --download-cache=$HOME/eggs -f http://dist.plone.org/thirdparty/ docutils==0.8.1

# install Zope
wget http://old.zope.org/Products/Zope/2.9.12/Zope-2.9.12-final.tgz
tar xzf Zope-${zope_version}.tgz
cd Zope-${zope_version}
./configure --with-python=../sandbox/bin/python2.4
make
make inplace
cd ..
./Zope-${zope_version}/bin/mkzopeinstance.py -d zinstance -u $login:$password

# install CPS
cd zinstance
wget http://download.cps-cms.org/CPS-${version}/CPS-Full-${version}.tgz
tar xzf CPS-Full-${version}.tgz
mv CPS-Full-${version}/* Products/

# change the port
sed -i "s/address 8080/address $PORT/" "etc/zope.conf"

cd ..

# create the startup script
cat > start.sh << EOF
#!/usr/bin/env sh
exec zinstance/bin/runzope
EOF

# create a popup for installation instruction
cat > popup.html << EOF
<p>To start using CPS, you must create a CPS site. Do the following:</p>
<ol>
    <li>Click on <a href="manage_main">Zope Management Interface</a> and connect with the password you chose</li>
    <li>In the top right selection list, select "CPSDefault Site"</li>
    <li>Fill in the required informations for your CPS site.<br/>
        Note that the Site id will be visible in the URL<li/>
    <li>Choose the extensions you need by checking the wanted checkboxes<li/>
    <li>Click on the "Add" button on the bottom of the page, you should then see your site in the list</li>
    <li>Click on your CPS site in the list</li>
    <li>Click on the "View" tab on the top</li>
    <li>Enjoy!</li>
</ol>
EOF
