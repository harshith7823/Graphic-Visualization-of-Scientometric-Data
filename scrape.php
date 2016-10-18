<?php

$begin_url =$argv[1];
for($i=2;$i<count($argv);$i++)
	$begin_url=$begin_url."&".$argv[$i];
$content = file_get_contents($begin_url);
// $content = file_get_contents("page1.txt")
echo $content;
//--------
// $fp = fopen("data1.txt","wb");
// fwrite($fp,$content);
// fclose($fp);
?>