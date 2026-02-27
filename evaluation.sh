# !bin/bash

mkdir -p ./results

python evaluation.py --trace ../ChampSim/bin/redis.000.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.001.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.002.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.003.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.004.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.005.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.006.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.007.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.008.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/redis.009.champsimtrace.trace --query-ms 1000 --out-dir ./results

python evaluation.py --trace ../ChampSim/bin/pagerank.000.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/pagerank.000.champsimtrace.trace --query-ms 100 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/pagerank.000.champsimtrace.trace --query-ms 1 --out-dir ./results

python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-2421B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-3477B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-4004B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-4248B.champsimtrace.trace --query-ms 1000 --out-dir ./results

python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-10881B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-1176B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-1B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-7084B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-8225B.champsimtrace.trace --query-ms 1000 --out-dir ./results

python evaluation.py --trace ../ChampSim/bin/654.roms_s-1007B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-1021B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-1070B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-1390B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-1613B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-293B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-294B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-523B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/654.roms_s-842B.champsimtrace.trace --query-ms 1000 --out-dir ./results

python evaluation.py --trace ../ChampSim/bin/429.mcf-184B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/429.mcf-192B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/429.mcf-217B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/429.mcf-22B.champsimtrace.trace --query-ms 1000 --out-dir ./results
python evaluation.py --trace ../ChampSim/bin/429.mcf-51B.champsimtrace.trace --query-ms 1000 --out-dir ./results



#############

#python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-2421B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-3477B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-4004B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/607.cactuBSSN_s-4248B.champsimtrace.trace --query-ms 100 --out-dir ./results

#python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-10881B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-1176B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-1B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-7084B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/649.fotonik3d_s-8225B.champsimtrace.trace --query-ms 100 --out-dir ./results

#python evaluation.py --trace ../ChampSim/bin/654.roms_s-1007B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-1021B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-1070B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-1390B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-1613B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-293B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-294B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-523B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/654.roms_s-842B.champsimtrace.trace --query-ms 100 --out-dir ./results

#python evaluation.py --trace ../ChampSim/bin/429.mcf-184B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/429.mcf-192B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/429.mcf-217B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/429.mcf-22B.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/429.mcf-51B.champsimtrace.trace --query-ms 100 --out-dir ./results

#python evaluation.py --trace ../ChampSim/bin/redis.000.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.001.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.002.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.003.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.004.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.005.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.006.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.007.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.008.champsimtrace.trace --query-ms 100 --out-dir ./results
#python evaluation.py --trace ../ChampSim/bin/redis.009.champsimtrace.trace --query-ms 100 --out-dir ./results

#python evaluation.py --trace ../ChampSim/bin/pagerank.000.champsimtrace.trace --query-ms 100 --out-dir ./results
