---
substitutions:
  figure0figno_subfloat0: |
    ```{figure} path/to/figure/1.suffix
    :name: fig:no_subfloat-0
    Overall Caption no subfloat.
    ```
  figure0figno_subfloat1: |
    ```{figure} path/to/figure/2.suffix
    :name: fig:no_subfloat-1
    Overall Caption no subfloat.
    ```
  figure2figfigure_in_table0: |
    ```{figure} path/to/figure/1.suffix
    :name: fig:figure_in_table-0
    :width: 45%
    Overall Caption
    ```
  figure2figfigure_in_table1: |
    ```{figure} path/to/figure/2.suffix
    :name: fig:figure_in_table-1
    :width: 50%
    Overall Caption
    ```
---

````{list-table} Overall Caption no subfloat. Overall Caption no subfloat.
:name: fig:no_subfloat
* - {{ figure0figno_subfloat0 }}
* - {{ figure0figno_subfloat1 }}
````

\

\

```{figure} graph1
:name: fig:y equals x
:width: 100%
$y=x$
```

```{figure} graph2
:name: fig:three sin x
:width: 100%
$y=3sinx$
```

```{figure} graph3
:name: fig:five over x
:width: 100%
$y=5/x$
```

```{list-table} Overall CaptionOverall Caption
:name: fig:figure_in_table
* - {{figure2figfigure_in_table0}}
  - {{figure2figfigure_in_table1}}
```