#!/bin/bash
cp bad.h-orig bad.h
./work.py lint --all
diff bad.h good.h
