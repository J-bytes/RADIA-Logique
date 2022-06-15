branch_name="$(git symbolic-ref HEAD 2>/dev/null)"
if (branch_name="main") || (branch_name="master") then
   python -m pylint  --verbose ./CheXpert2
   code=$?
   exit 0
fi

echo "Not on main ; pylint wont run"
exit 0
