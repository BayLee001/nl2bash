grammar Commands;

command : find1
	    | find2
	    | mv1
	    | mv2
	    | sort1
	    | grep1
	    | egrep1
	    | cp1
	    | cp2
	    | ls1
	    | tar1
	    | tar2
	    | tar3
	    | tar4
	    | tar5
	    | xargs1
	    | sed1
	    | sed2
	    | awk1
	    | rm1
	    | cd1
	    | wc1
	    | chmod1
	    | chmod2
	    | chmod3
	    | chmod4
	    | chmod5
	    | chown1
	    | head1
	    | tail1
	    | seq1
	    | unlink1
	    | cat1
	    | zip1
	    | unzip1
	    | du1
	    | echo1
	    | diff1
	    | comm1
	    | sh1
	    ;

find1 : 'find' ((find_op0) | (find_op1) | (find_op2) | (find_op3) | (find_op4) | (find_op5) | (find_op6))* (File=STRING)+ (find_expression)*;
find2 : 'find' ((find_op0) | (find_op1) | (find_op2) | (find_op3) | (find_op4) | (find_op5))* '-f' File=STRING ((find_op7))* (find_expression)*;
mv1 : 'mv' ((mv_op0) | (mv_op1))* File=STRING File=STRING;
mv2 : 'mv' ((mv_op0) | (mv_op1))* (File=STRING)+ File=STRING;
sort1 : 'sort' ((sort_op0) | (sort_op1) | (sort_op2) | (sort_op3) | (sort_op4) | (sort_op5) | (sort_op6) | (sort_op7) | (sort_op8) | (sort_op9) | (sort_op10) | (sort_op11) | (sort_op12) | (sort_op13) | (sort_op14) | (sort_op15) | (sort_op16) | (sort_op17) | (sort_op18))*;
grep1 : 'grep' ((grep_op0) | (grep_op1) | (grep_op2) | (grep_op3) | (grep_op4) | (grep_op5) | (grep_op6) | (grep_op7) | (grep_op8) | (grep_op9) | (grep_op10) | (grep_op11) | (grep_op12) | (grep_op13) | (grep_op14) | (grep_op15) | (grep_op16) | (grep_op17) | (grep_op18) | (grep_op19) | (grep_op20) | (grep_op21) | (grep_op22) | (grep_op23) | (grep_op24) | (grep_op25) | (grep_op26) | (grep_op27) | (grep_op28) | (grep_op29) | (grep_op30) | (grep_op31) | (grep_op32) | (grep_op33) | (grep_op34) | (grep_op35) | (grep_op36) | (grep_op37) | (grep_op38) | (grep_op39) | (grep_op40))*;
egrep1 : 'egrep' ((egrep_op0) | (egrep_op1) | (egrep_op2) | (egrep_op3) | (egrep_op4) | (egrep_op5) | (egrep_op6) | (egrep_op7) | (egrep_op8) | (egrep_op9) | (egrep_op10) | (egrep_op11) | (egrep_op12) | (egrep_op13) | (egrep_op14) | (egrep_op15) | (egrep_op16) | (egrep_op17) | (egrep_op18) | (egrep_op19) | (egrep_op20) | (egrep_op21) | (egrep_op22) | (egrep_op23) | (egrep_op24) | (egrep_op25) | (egrep_op26) | (egrep_op27) | (egrep_op28) | (egrep_op29) | (egrep_op30) | (egrep_op31) | (egrep_op32) | (egrep_op33) | (egrep_op34) | (egrep_op35) | (egrep_op36) | (egrep_op37) | (egrep_op38) | (egrep_op39) | (egrep_op40))*;
cp1 : 'cp' ((cp_op1) | (cp_op2) | (cp_op3) | (cp_op4) | (cp_op5) | (cp_op6))* File=STRING File=STRING;
cp2 : 'cp' ((cp_op1) | (cp_op2) | (cp_op3) | (cp_op4) | (cp_op5) | (cp_op6))* (File=STRING)+ File=STRING;
ls1 : 'ls' ((ls_op0) | (ls_op1) | (ls_op2) | (ls_op3) | (ls_op4) | (ls_op5) | (ls_op6) | (ls_op7) | (ls_op8) | (ls_op9) | (ls_op10) | (ls_op11) | (ls_op12) | (ls_op13) | (ls_op14) | (ls_op15) | (ls_op16) | (ls_op17) | (ls_op18) | (ls_op19) | (ls_op20) | (ls_op21) | (ls_op22) | (ls_op23) | (ls_op24) | (ls_op25) | (ls_op26) | (ls_op27) | (ls_op28) | (ls_op29) | (ls_op30) | (ls_op31) | (ls_op32) | (ls_op33) | (ls_op34) | (ls_op35) | (ls_op36) | (ls_op37) | (ls_op38))*;
tar1 : 'tar' '-c' ((tar_op0) | (tar_op1) | (tar_op2) | (tar_op3) | (tar_op4) | (tar_op5) | (tar_op6) | (tar_op7) | (tar_op8) | (tar_op9) | (tar_op10) | (tar_op11) | (tar_op12) | (tar_op13) | (tar_op14) | (tar_op15) | (tar_op16) | (tar_op17) | (tar_op18) | (tar_op19) | (tar_op20) | (tar_op21) | (tar_op22) | (tar_op23) | (tar_op24) | (tar_op25) | (tar_op26) | (tar_op27) | (tar_op28) | (tar_op29) | (tar_op30) | (tar_op31) | (tar_op32) | (tar_op35))*;
tar2 : 'tar' '-r' '-f' File=STRING ((tar_op0) | (tar_op1) | (tar_op2) | (tar_op3) | (tar_op4) | (tar_op5) | (tar_op6) | (tar_op7) | (tar_op8) | (tar_op9) | (tar_op11) | (tar_op12) | (tar_op13) | (tar_op14) | (tar_op15) | (tar_op16) | (tar_op17) | (tar_op18) | (tar_op19) | (tar_op20) | (tar_op21) | (tar_op22) | (tar_op23) | (tar_op24) | (tar_op25) | (tar_op26) | (tar_op27) | (tar_op28) | (tar_op29) | (tar_op35))*;
tar3 : 'tar' '-u' '-f' File=STRING ((tar_op0) | (tar_op1) | (tar_op3) | (tar_op36) | (tar_op5) | (tar_op8) | (tar_op9) | (tar_op12) | (tar_op13) | (tar_op14) | (tar_op15) | (tar_op16) | (tar_op17) | (tar_op19) | (tar_op20) | (tar_op21) | (tar_op22) | (tar_op23) | (tar_op24) | (tar_op25) | (tar_op26) | (tar_op27) | (tar_op28) | (tar_op29) | (tar_op35))*;
tar4 : 'tar' '-t' ((tar_op0) | (tar_op1) | (tar_op3) | (tar_op5) | (tar_op8) | (tar_op9) | (tar_op12) | (tar_op37) | (tar_op21) | (tar_op22) | (tar_op38) | (tar_op23) | (tar_op24) | (tar_op25) | (tar_op26) | (tar_op27) | (tar_op28) | (tar_op29) | (tar_op39))*;
tar5 : 'tar' '-x' ((tar_op0) | (tar_op1) | (tar_op40) | (tar_op3) | (tar_op5) | (tar_op8) | (tar_op9) | (tar_op41) | (tar_op42) | (tar_op12) | (tar_op43) | (tar_op44) | (tar_op37) | (tar_op19) | (tar_op21) | (tar_op22) | (tar_op45) | (tar_op38) | (tar_op46) | (tar_op47) | (tar_op23) | (tar_op24) | (tar_op48) | (tar_op25) | (tar_op26) | (tar_op27) | (tar_op28) | (tar_op29) | (tar_op39))*;
xargs1 : 'xargs' ((xargs_op0) | (xargs_op1) | (xargs_op2) | (xargs_op3) | (xargs_op4) | (xargs_op6) | (xargs_op7) | (xargs_op8) | (xargs_op10) | (xargs_op11) | (xargs_op12) | (xargs_op14))*;
sed1 : 'sed' ((sed_op0) | (sed_op1) | (sed_op2) | (sed_op3))* String=STRING ((sed_op4))*;
sed2 : 'sed' ((sed_op0) | (sed_op1) | (sed_op2) | (sed_op3) | (sed_op5) | (sed_op6) | (sed_op7) | (sed_op4))*;
awk1 : 'awk' ((awk_op0) | (awk_op1) | (awk_op4) | (awk_op5))*;
rm1 : 'rm' ((rm_op0) | (rm_op1) | (rm_op2) | (rm_op3) | (rm_op4) | (rm_op5) | (rm_op6) | (rm_op7))* (File=STRING)+;
cd1 : 'cd' ((cd_op0) | (cd_op1))*;
wc1 : 'wc' ((wc_op0) | (wc_op1) | (wc_op2) | (wc_op3) | (wc_op4))*;
chmod1 : 'chmod' ((chmod_op0) | (chmod_op1) | (chmod_op3))* Permission=STRING (File=STRING)+;
chmod2 : 'chmod' ((chmod_op0) | (chmod_op1) | (chmod_op3) | (chmod_op7))* 'ACE' (File=STRING)+;
chmod3 : 'chmod' ((chmod_op0) | (chmod_op8) | (chmod_op1) | (chmod_op3) | (chmod_op9))* (File=STRING)+;
chmod4 : 'chmod' ((chmod_op0) | (chmod_op8) | (chmod_op1) | (chmod_op3) | (chmod_op10))* (File=STRING)+;
chmod5 : 'chmod' ((chmod_op0) | (chmod_op8) | (chmod_op1) | (chmod_op3) | (chmod_op11))* (File=STRING)+;
chown1 : 'chown' ((chown_op0) | (chown_op1) | (chown_op2) | (chown_op4))* String=STRING (File=STRING)+;
head1 : 'head' ((head_op2) | (head_op3))*;
tail1 : 'tail' ((tail_op0) | (tail_op1) | (tail_op5) | (tail_op6))*;
seq1 : 'seq' ((seq_op0) | (seq_op1) | (seq_op2) | (seq_op3) | (seq_op5))* String=STRING;
unlink1 : 'unlink' File=STRING;
cat1 : 'cat' ((cat_op0) | (cat_op1) | (cat_op2) | (cat_op3) | (cat_op4) | (cat_op5) | (cat_op6) | (cat_op7))*;
zip1 : 'zip' ((zip_op0) | (zip_op1) | (zip_op2) | (zip_op3) | (zip_op4) | (zip_op5) | (zip_op6) | (zip_op7) | (zip_op8) | (zip_op9) | (zip_op10) | (zip_op11) | (zip_op12) | (zip_op13) | (zip_op14) | (zip_op15) | (zip_op16) | (zip_op17) | (zip_op18) | (zip_op19) | (zip_op20) | (zip_op21) | (zip_op22) | (zip_op23) | (zip_op24) | (zip_op25) | (zip_op26) | (zip_op27) | (zip_op28) | (zip_op29) | (zip_op30) | (zip_op31) | (zip_op32) | (zip_op33) | (zip_op34) | (zip_op35) | (zip_op36) | (zip_op37) | (zip_op39) | (zip_op40))*;
unzip1 : 'unzip' ((unzip_op0) | (unzip_op1) | (unzip_op2) | (unzip_op3) | (unzip_op4) | (unzip_op5) | (unzip_op6) | (unzip_op7) | (unzip_op8) | (unzip_op9) | (unzip_op10) | (unzip_op11) | (unzip_op12) | (unzip_op13) | (unzip_op14) | (unzip_op15) | (unzip_op16) | (unzip_op17) | (unzip_op18) | (unzip_op19) | (unzip_op20) | (unzip_op21) | (unzip_op22) | (unzip_op23))* File=STRING ((unzip_op24) | (unzip_op25) | (unzip_op26))*;
du1 : 'du' ((du_op0) | (du_op2) | (du_op3) | (du_op4) | (du_op5) | (du_op6) | (du_op7))*;
echo1 : 'echo' ((echo_op0) | (echo_op1))*;
diff1 : 'diff' ((diff_op0))* (File=STRING)+;
comm1 : 'comm' ((comm_op0) | (comm_op1) | (comm_op2) | (comm_op3))* File=STRING File=STRING;
sh1 : 'sh' ((sh_op0) | (sh_op1))*;

find_expression : '-true'
                | '-false'
                | find_primitive_exp
                | '(' find_expression ')'
                | '-not' find_expression
                | find_expression '-and' find_expression
                | find_expression '-or' find_expression
                | '!' find_expression
                ;

find_primitive_exp : '-not' String=STRING
                   | '-Bmin' Number=STRING
                   | '-Bnewer' File=STRING
                   | '-Btime' Time=STRING
                   | '-acl'
                   | '-amin' Number=STRING
                   | '-anewer' File=STRING
                   | '-a' '-t' '-i' '-m' '-e'  Time=STRING
                   | '-cmin' Number=STRING
                   | '-cnewer' File=STRING
                   | '-ctime' Number=STRING
                   | '-d'
                   | '-daystart'
                   | '-delete'
                   | '-depth'
                   | '-depth' Number=STRING
                   | '-empty'
                   | '-exec' String=STRING (find_primitive_exp_op0)? ';'
                   | '-exec' String=STRING (find_primitive_exp_op0)? ('{}')+
                   | '-execdir' String=STRING (find_primitive_exp_op0)? ';'
                   | '-execdir' String=STRING (find_primitive_exp_op0)?
                   | '-flags' '-'String=STRING
                   | '-flags' '+'String=STRING
                   | '-flags' String=STRING
                   | '-fstype' String=STRING
                   | '-gid' String=STRING
                   | '-group' String=STRING
                   | '-ignore_readdir_race'
                   | '-ilname' String=STRING
                   | '-ilname' String=STRING
                   | '-iname' String=STRING
                   | '-inum' Number=STRING
                   | '-ipath' String=STRING
                   | '-iregex' String=STRING
                   | '-iwholename' String=STRING
                   | '-links' Number=STRING
                   | '-lname' String=STRING
                   | '-ls'
                   | '-maxdepth' Number=STRING
                   | '-mindepth' Number=STRING
                   | '-mmin' Number=STRING
                   | '-mnewer' File=STRING
                   | '-mount'
                   | '-mtime' Time=STRING
                   | '-name' String=STRING
                   | '-newer' File=STRING
                   | '-newerXY' File=STRING
                   | '-nogroup'
                   | '-noignore_readdir_race'
                   | '-noleaf'
                   | '-nouser'
                   | '-ok' String=STRING (find_primitive_exp_op0)? ';'
                   | '-okdir' String=STRING (find_primitive_exp_op0)? ';'
                   | '-path' String=STRING
                   | '-perm' Permission=STRING
                   | '-perm' '-'Permission=STRING
                   | '-perm' '+'Permission=STRING
                   | '-print'
                   | '-print0'
                   | '-printf' String=STRING
                   | '-prune'
                   | '-regex' String=STRING
                   | '-samefile' String=STRING
                   | '-size' Size=STRING
                   | '-type' String=STRING
                   | '-xtype' String=STRING
                   | '-uid' String=STRING
                   | '-user' String=STRING
                   | '-wholename' String=STRING
                   | '-xattr'
                   | '-xattrname' String=STRING
                   ;



awk_op0 : '-F' String=STRING ;
awk_op1 : '-v' String=STRING ;
awk_op2 : (String=STRING)+;
awk_op3 : '-f' File=STRING ;
awk_op4 : awk_op2 | awk_op3;
awk_op5 : (File=STRING)+;
cat_op0 : '-b';
cat_op1 : '-e';
cat_op2 : '-n';
cat_op3 : '-s';
cat_op4 : '-t';
cat_op5 : '-u';
cat_op6 : '-v';
cat_op7 : (File=STRING)+;
cd_op0 : '-L' | '-P';
cd_op1 : File=STRING;
chmod_op0 : '-f';
chmod_op1 : '-v';
chmod_op10 : '-C';
chmod_op11 : '-N';
chmod_op2 : '-H' | '-L' | '-P';
chmod_op3 : '-R' (chmod_op2)? ;
chmod_op4 : '-'Number=STRING;
chmod_op5 : '+'Number=STRING;
chmod_op6 : '='Number=STRING;
chmod_op7 : chmod_op4 | chmod_op5 | chmod_op6;
chmod_op8 : '-h';
chmod_op9 : '-E';
chown_op0 : '-f';
chown_op1 : '-h';
chown_op2 : '-v';
chown_op3 : '-H' | '-L' | '-P';
chown_op4 : '-R' (chown_op3)? ;
comm_op0 : '-1';
comm_op1 : '-2';
comm_op2 : '-3';
comm_op3 : '-i';
cp_op0 : '-H' | '-L' | '-P';
cp_op1 : '-R' (cp_op0)? ;
cp_op2 : '-f' '-i'  | '-n';
cp_op3 : '-a';
cp_op4 : '-p';
cp_op5 : '-v';
cp_op6 : '-X';
diff_op0 : (Unknown=STRING)+;
du_op0 : '-H' | '-L' | '-P';
du_op1 : '-d' Number=STRING ;
du_op2 : '-a' | '-s' | du_op1;
du_op3 : '-c';
du_op4 : '-h' | '-k' | '-m' | '-g';
du_op5 : '-x';
du_op6 : '-I' Number=STRING ;
du_op7 : (File=STRING)+;
echo_op0 : '-n';
echo_op1 : (String=STRING)+;
egrep_op0 : '-a';
egrep_op1 : '-b';
egrep_op10 : '-I';
egrep_op11 : '-i';
egrep_op12 : '-J';
egrep_op13 : '-L';
egrep_op14 : '-l';
egrep_op15 : '-m';
egrep_op16 : '-n';
egrep_op17 : '-O';
egrep_op18 : '-o';
egrep_op19 : '-p';
egrep_op2 : '-c';
egrep_op20 : '-q';
egrep_op21 : '-R';
egrep_op22 : '-S';
egrep_op23 : '-s';
egrep_op24 : '-U';
egrep_op25 : '-V';
egrep_op26 : '-v';
egrep_op27 : '-w';
egrep_op28 : '-x';
egrep_op29 : '-Z';
egrep_op3 : '-d';
egrep_op30 : '-A' Number=STRING ;
egrep_op31 : '-B' Number=STRING ;
egrep_op32 : '-C' Number=STRING ;
egrep_op33 : '-e' String=STRING ;
egrep_op34 : '-f' File=STRING ;
egrep_op35 : '--context=' (Number=STRING)*;
egrep_op36 : '--label';
egrep_op37 : '--line-buffered';
egrep_op38 : '--null';
egrep_op39 : String=STRING;
egrep_op4 : '-D';
egrep_op40 : (File=STRING)+;
egrep_op5 : '-E';
egrep_op6 : '-F';
egrep_op7 : '-G';
egrep_op8 : '-H';
egrep_op9 : '-h';
find_op0 : '-H' | '-L' | '-P';
find_op1 : '-E';
find_op2 : '-X';
find_op3 : '-d';
find_op4 : '-s';
find_op5 : '-x';
find_op6 : '-f' File=STRING ;
find_op7 : (File=STRING)+;
find_primitive_exp_op0 : (String=STRING)+;
grep_op0 : '-a';
grep_op1 : '-b';
grep_op10 : '-I';
grep_op11 : '-i';
grep_op12 : '-J';
grep_op13 : '-L';
grep_op14 : '-l';
grep_op15 : '-m';
grep_op16 : '-n';
grep_op17 : '-O';
grep_op18 : '-o';
grep_op19 : '-p';
grep_op2 : '-c';
grep_op20 : '-q';
grep_op21 : '-R';
grep_op22 : '-S';
grep_op23 : '-s';
grep_op24 : '-U';
grep_op25 : '-V';
grep_op26 : '-v';
grep_op27 : '-w';
grep_op28 : '-x';
grep_op29 : '-Z';
grep_op3 : '-d';
grep_op30 : '-A' Number=STRING ;
grep_op31 : '-B' Number=STRING ;
grep_op32 : '-C' Number=STRING ;
grep_op33 : '-e' String=STRING ;
grep_op34 : '-f' File=STRING ;
grep_op35 : '--context=' (Number=STRING)*;
grep_op36 : '--label';
grep_op37 : '--line-buffered';
grep_op38 : '--null';
grep_op39 : String=STRING;
grep_op4 : '-D';
grep_op40 : (File=STRING)+;
grep_op5 : '-E';
grep_op6 : '-F';
grep_op7 : '-G';
grep_op8 : '-H';
grep_op9 : '-h';
head_op0 : '-n' Number=STRING ;
head_op1 : '-c' Number=STRING ;
head_op2 : head_op0 | head_op1;
head_op3 : (File=STRING)+;
ls_op0 : '-A';
ls_op1 : '-B';
ls_op10 : '-S';
ls_op11 : '-T';
ls_op12 : '-U';
ls_op13 : '-W';
ls_op14 : '-@';
ls_op15 : '-a';
ls_op16 : '-b';
ls_op17 : '-c';
ls_op18 : '-d';
ls_op19 : '-e';
ls_op2 : '-C';
ls_op20 : '-f';
ls_op21 : '-g';
ls_op22 : '-h';
ls_op23 : '-i';
ls_op24 : '-k';
ls_op25 : '-l';
ls_op26 : '-m';
ls_op27 : '-n';
ls_op28 : '-o';
ls_op29 : '-p';
ls_op3 : '-F';
ls_op30 : '-q';
ls_op31 : '-r';
ls_op32 : '-s';
ls_op33 : '-t';
ls_op34 : '-u';
ls_op35 : '-w';
ls_op36 : '-x';
ls_op37 : '-1';
ls_op38 : (File=STRING)+;
ls_op4 : '-G';
ls_op5 : '-H';
ls_op6 : '-L';
ls_op7 : '-O';
ls_op8 : '-P';
ls_op9 : '-R';
mv_op0 : '-f' | '-i' | '-n';
mv_op1 : '-v';
rm_op0 : '-d';
rm_op1 : '-f';
rm_op2 : '-i';
rm_op3 : '-P';
rm_op4 : '-R';
rm_op5 : '-r';
rm_op6 : '-v';
rm_op7 : '-W';
sed_op0 : '-E';
sed_op1 : '-a';
sed_op2 : '-l';
sed_op3 : '-n';
sed_op4 : (File=STRING)+;
sed_op5 : '-e' String=STRING ;
sed_op6 : '-f' File=STRING ;
sed_op7 : '-i' String=STRING ;
seq_op0 : '-w';
seq_op1 : '-f' String=STRING ;
seq_op2 : '-s' String=STRING ;
seq_op3 : '-t' String=STRING ;
seq_op4 : Number=STRING;
seq_op5 : String=STRING (seq_op4)? ;
sh_op0 : (String=STRING)+;
sh_op1 : (File=STRING)+;
sort_op0 : '-b';
sort_op1 : '-d';
sort_op10 : '-m';
sort_op11 : '-o';
sort_op12 : '-s';
sort_op13 : '-S';
sort_op14 : '-t';
sort_op15 : '-T';
sort_op16 : '-u';
sort_op17 : '-z';
sort_op18 : (File=STRING)+;
sort_op2 : '-f';
sort_op3 : '-g';
sort_op4 : '-i';
sort_op5 : '-M';
sort_op6 : '-n';
sort_op7 : '-r';
sort_op8 : '-c';
sort_op9 : '-k';
tail_op0 : '-F' | '-f' | '-r';
tail_op1 : '-q';
tail_op2 : '-b' Number=STRING ;
tail_op3 : '-c' Number=STRING ;
tail_op4 : '-n' Number=STRING ;
tail_op5 : tail_op2 | tail_op3 | tail_op4;
tail_op6 : (File=STRING)+;
tar_op0 : '-b' Size=STRING ;
tar_op1 : '-C' File=STRING ;
tar_op10 : '-j';
tar_op11 : '-L';
tar_op12 : '-l';
tar_op13 : '-n';
tar_op14 : '--newer' Date=STRING ;
tar_op15 : '--newer-mtime' Date=STRING ;
tar_op16 : '--newer-than' File=STRING ;
tar_op17 : '--newer-mtime-than' File=STRING ;
tar_op18 : '--nodump';
tar_op19 : '-o';
tar_op2 : '--check-links';
tar_op20 : '--one-file-system';
tar_op21 : '--options' String=STRING ;
tar_op22 : '-P';
tar_op23 : '-s' String=STRING ;
tar_op24 : '-T' File=STRING ;
tar_op25 : '--use-compress-program' String=STRING ;
tar_op26 : '-v';
tar_op27 : '--version';
tar_op28 : '-w';
tar_op29 : '-X' File=STRING ;
tar_op3 : '--exclude' String=STRING ;
tar_op30 : '-y';
tar_op31 : '-z';
tar_op32 : '-Z';
tar_op33 : (File=STRING)+;
tar_op34 : (File=STRING)+;
tar_op35 : tar_op33 | tar_op34;
tar_op36 : '--format' String=STRING ;
tar_op37 : '-O';
tar_op38 : '-q';
tar_op39 : (String=STRING)+;
tar_op4 : '--format' TarFormat=STRING ;
tar_op40 : '--chroot';
tar_op41 : '-k';
tar_op42 : '--keep-newer-files';
tar_op43 : '-m';
tar_op44 : '--numeric-owner';
tar_op45 : '-p';
tar_op46 : '-S';
tar_op47 : '--strip-components' Number=STRING ;
tar_op48 : '-U';
tar_op5 : '-f' File=STRING ;
tar_op6 : '-H';
tar_op7 : '-h';
tar_op8 : '-I';
tar_op9 : '--include' String=STRING ;
unzip_op0 : '-Z';
unzip_op1 : '-c';
unzip_op10 : '-a';
unzip_op11 : '-b';
unzip_op12 : '-j';
unzip_op13 : '-n';
unzip_op14 : '-o';
unzip_op15 : '-q';
unzip_op16 : '-s';
unzip_op17 : '-C';
unzip_op18 : '-K';
unzip_op19 : '-L';
unzip_op2 : '-f';
unzip_op20 : '-M';
unzip_op21 : '-V';
unzip_op22 : '-W';
unzip_op23 : '-X';
unzip_op24 : (File=STRING)+;
unzip_op25 : '-x' (File=STRING)+ ;
unzip_op26 : '-d' File=STRING ;
unzip_op3 : '-l';
unzip_op4 : '-p';
unzip_op5 : '-t';
unzip_op6 : '-T';
unzip_op7 : '-u';
unzip_op8 : '-v';
unzip_op9 : '-z';
wc_op0 : '-c';
wc_op1 : '-l';
wc_op2 : '-m';
wc_op3 : '-w';
wc_op4 : (File=STRING)+;
xargs_op0 : '-0';
xargs_op1 : '-o';
xargs_op10 : '-n' Number=STRING (xargs_op9)? ;
xargs_op11 : '-P' Number=STRING ;
xargs_op12 : '-s' Size=STRING ;
xargs_op13 : (String=STRING)+;
xargs_op14 : String=STRING (xargs_op13)? ;
xargs_op2 : '-p';
xargs_op3 : '-t';
xargs_op4 : '-E' String=STRING ;
xargs_op5 : '-R' Number=STRING ;
xargs_op6 : '-I' String=STRING (xargs_op5)? ;
xargs_op7 : '-J' String=STRING ;
xargs_op8 : '-L' Number=STRING ;
xargs_op9 : '-x';
zip_op0 : '-a';
zip_op1 : '-A';
zip_op10 : '-g';
zip_op11 : '-h';
zip_op12 : '-j';
zip_op13 : '-k';
zip_op14 : '-l';
zip_op15 : '-L';
zip_op16 : '-m';
zip_op17 : '-o';
zip_op18 : '-q';
zip_op19 : '-r';
zip_op2 : '-B';
zip_op20 : '-R';
zip_op21 : '-S';
zip_op22 : '-T';
zip_op23 : '-u';
zip_op24 : '-v';
zip_op25 : '-V';
zip_op26 : '-w';
zip_op27 : '-X';
zip_op28 : '-y';
zip_op29 : '-z';
zip_op3 : '-c';
zip_op30 : '-@';
zip_op31 : '-!';
zip_op32 : '-$';
zip_op33 : '--longoption';
zip_op34 : '-b' File=STRING ;
zip_op35 : '-n' String=STRING ;
zip_op36 : '-t' Date=STRING ;
zip_op37 : '-t' '-t'  Date=STRING ;
zip_op38 : (File=STRING)+;
zip_op39 : File=STRING (zip_op38)? ;
zip_op4 : '-d';
zip_op40 : '-xi' String=STRING ;
zip_op5 : '-D';
zip_op6 : '-e';
zip_op7 : '-E';
zip_op8 : '-f';
zip_op9 : '-F';

//File : STRING;
//Permission: STRING;
//Size: STRING;
//Time: STRING;
//Argument: STRING;
//Utility: STRING;
//Number: STRING;
//Pattern: STRING;
//String : STRING;
//STRING : ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '.' | '_' | '/' ) + ;
STRING : ( ~' ' ) + ;
WS : [ \t\n\r] + -> skip;