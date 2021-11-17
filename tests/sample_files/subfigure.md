---
substitutions:
  figure-0:fig:no_subfloat-0: |
    ```{figure} path/to/figure/1.suffix
    :name: "fig:no_subfloat-0"
    Overall Caption no subfloat.
    ```
  figure-0:fig:no_subfloat-1: |
    ```{figure} path/to/figure/2.suffix
    :name: "fig:no_subfloat-1"
    Overall Caption no subfloat.
    ```
---

````{list-table} Overall Caption no subfloat. Overall Caption no subfloat.
:name: "fig:no_subfloat"
* - {{ figure-0:fig:no_subfloat-0 }}
* - {{ figure-0:fig:no_subfloat-1 }}
````

\

\

```{figure} graph1
:name: "fig:y equals x"
:width: 100%
$y=x$
```

```{figure} graph2
:name: "fig:three sin x"
:width: 100%
$y=3sinx$
```

'' [\[fig:three sin x\]]{#fig:three sin x label="fig:three sin x"}

```{figure} graph3
:name: "fig:five over x"
:width: 100%
$y=5/x$
```