gaurav@WT-W-HHLKD63:~/projects/grants-stack$ docker compose exec app whoami
appuser
gaurav@WT-W-HHLKD63:~/projects/grants-stack$ docker stats --no-stream
CONTAINER ID   NAME                   CPU %     MEM USAGE / LIMIT   MEM %     NET I/O           BLOCK I/O        PIDS
3c8328a1b0ab   grants-stack-proxy-1   0.00%     6.965MiB / 32MiB    21.77%    2.1kB / 1.4kB     1.64MB / 4.1kB   9
40afd3f16f20   grants-stack-app-1     0.01%     55.05MiB / 200MiB   27.53%    4.57kB / 3.36kB   9.61MB / 4.1kB   3
cf52616d2c26   grants-stack-db-1      0.02%     21.7MiB / 256MiB    8.47%     4.34kB / 3.01kB   11.9MB / 618kB   6
gaurav@WT-W-HHLKD63:~/projects/grants-stack$ docker images
                                                                                                                                                                                               i Info →   U  In Use
IMAGE                                 ID             DISK USAGE   CONTENT SIZE   EXTRA
gcr.io/k8s-minikube/kicbase:v0.0.50   6da180ef5035       1.37GB             0B
grants-stack-app:latest               a2ba8e6193f6       62.5MB             0B
nginx:1.25-alpine                     501d84f5d064       48.3MB             0B
postgres:16-alpine                    75f5a96988cd        294MB             0B
gaurav@WT-W-HHLKD63:~/projects/grants-stack$
